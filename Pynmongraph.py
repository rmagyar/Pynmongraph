#!/usr/bin/env python3
"""
Copyright (c) 2015 Richard Magyar
Copyright (c) 2012-2015 Matthias Lee

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# TODO zoom to date
# TODO CPU bar charts (optimize number of CPU shown)
# TODO IOADAPT stacked graph
# TODO VIOS
# TODO Check if nmon files exists before parsing
#
# Module imports
#

import os
import sys
import platform
from shutil import rmtree
import argparse
import logging as log
import numpy as np
import datetime
import timeit
import glob
import matplotlib as mpl
import matplotlib.pyplot as plt

sysInfo = []
start = timeit.default_timer() # Measure total running time

#
# Report creation function
#

def createreport(outfiles, outpath):
    global hostname
    report = ""

    for i in sysInfo:
        if i[0] == "host":
            hostname = i[1]

    fname = hostname + "_report.html"

    reportpath = os.path.join(outpath, fname)

    try:
        report = open(reportpath, "w")
    except:
        log.error("Could not open report file!")
        exit()

    htmlheader = '''<html>
    <head><title>Nmon Report for %s </title></head>
    <body>
    <table>
    ''' % hostname

    # write out the html header
    report.write(htmlheader)

    report.write('<h1><center>Nmon report for ' + hostname + '</center></h1>')
    report.write('<center>Built on ' + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + '</center>')
    report.write('<center>Analysis time: ' + str("%.1f" % runtime) + ' seconds</center><br /><br />')

    omitfields = ['note0', 'note1', 'note2']
    s = set()

    report.write('<table border=1 align=center>')
    for i in sysInfo:
        if i[0] not in s and i[0] not in omitfields:
            if len(i) == 2:
                report.write('<tr><td>' + i[0] + '</td><td>' + i[1] + '</td></tr>')
            s.add(i[0])

    report.write('</table>')

    # Table of contents
    report.write('<a name="top"></a>')
    report.write('<table border=1 align=center>')
    report.write('<tr><td><center>Table of graphs</center></td></tr>')
    for f in outfiles:
        n = f.split("/")
        m = n[3].split(".")
        report.write('<tr><td><a href="#{}">{}</a></td></tr>'.format(m[0], m[0]))
    report.write('</table>')

    report.write('<table border=1 align=center>')
    for f in outfiles:
        n = f.split("/")
        m = n[3].split(".")
        report.write('''<tr>
        <td><a name="{}"></a><br /><br />
        <img src="{}" />
        <br /><center><a href="#top">top</a></center>
        </td>
        </tr>
        '''.format( m[0],os.path.relpath(f, outpath)))

    report.write('''</table>
</body>
</html>
''')
    report.close()

#
# Graph plotting
#

class Pynmonplotter:
    # Holds final 2D arrays of each stat
    processedData = {}

    def __init__(self, processeddata, outdir="./data/", debug=False):

        global hostname
        for i in sysInfo:
            if i[0] == "host":
                hostname = i[1]

        self.imgPath = os.path.join(outdir, hostname + "files")
        self.debug = debug
        self.processedData = processeddata
        if not (os.path.exists(self.imgPath)):
            try:
                os.makedirs(self.imgPath)
            except:
                log.error("Creating results dir:", self.imgPath)
                exit()

    def plotstats(self, todolist):
        outfiles = []
        if len(todolist) <= 0:
            log.error("Nothing to plot")
            exit()

        for stat, fields in todolist:
            if stat == "CPU_ALL":
                if stat in self.processedData:
                    log.debug("starting " + stat)
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["CPU_ALL"][0][1:]]
                    values = [(self.processedData["CPU_ALL"][1][1:], "usr"),
                              (self.processedData["CPU_ALL"][2][1:], "sys"),
                              (self.processedData["CPU_ALL"][3][1:], "wait"),
                              (self.processedData["CPU_ALL"][4][1:], "idle")]

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel="CPU load (%)", title=stat)
                    outfiles.append(fname)

            if stat == "PCPU_ALL":
                if stat in self.processedData:
                    log.debug("starting " + stat)
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["PCPU_ALL"][0][1:]]
                    values = [(self.processedData["PCPU_ALL"][1][1:], "usr"),
                              (self.processedData["PCPU_ALL"][2][1:], "sys"),
                              (self.processedData["PCPU_ALL"][3][1:], "wait"),
                              (self.processedData["PCPU_ALL"][4][1:], "idle"),
                              (self.processedData["PCPU_ALL"][5][1:], "enc")]

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel="Physical CPU load", title=stat)
                    outfiles.append(fname)

            elif stat == "LPAR":
                log.debug("starting " + stat)
                if stat in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["LPAR"][0][1:]]
                    values = [(self.processedData["LPAR"][1][1:], "phyc"), (self.processedData["LPAR"][5][1:], "enc"),
                              (self.processedData["LPAR"][20][1:], "folded"), (self.processedData["LPAR"][2][1:], "VP")]

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel="Physical CPU use", title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "POOL":
                log.debug("starting " + stat)
                if "LPAR" in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["LPAR"][0][1:]]
                    values = [(self.processedData["LPAR"][4][1:], "poolCPUs"),
                              (self.processedData["LPAR"][7][1:], "poolIdle")]

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel="Shared Pool usage", title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "PROC":
                log.debug("starting " + stat)
                if "LPAR" in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["PROC"][0][1:]]
                    values = [(self.processedData["PROC"][1][1:], "Runnable"),
                              (self.processedData["PROC"][2][1:], "Swap-in")]

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel="Processes", title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "DISKBUSY" or stat == "DISKREAD" or stat == "DISKWRITE" or stat == "DISKREADSERV" or stat == "DISKWRITESERV" or stat == "DISKRIO" or stat == "DISKWIO" or stat == "DISKRXFER" or stat == "DISKXFER" or stat == "DISKWAIT" or stat == "DISKBSIZE":
                log.debug("starting " + stat)
                if stat in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData[stat][0][1:]]

                    text = str(self.processedData[stat][0][0])
                    label = text.rpartition(' ')[0]

                    values = []
                    maxvalues = []
                    topdisks = []

                    if "top" in fields:
                        # Determine top disks
                        for i in self.processedData[stat]:
                            coltitle = i[:1][0]
                            for _ in fields:
                                if "hdisk" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    maxvalues.append((np.amax(read), coltitle))
                        # Sorting array with max values
                        dtype = [('value', float), ('hdisk', 'U11')]
                        a = np.array(maxvalues, dtype=dtype)
                        sortedvalues = np.sort(a, order='value')
                        sortedvalues = sortedvalues[::-1]

                        numdisks = len(sortedvalues)
                        if numdisks > 5:
                            numdisks = 5

                        for i in range(0, numdisks):
                            topdisks.append(sortedvalues[i][1])

                        log.debug(topdisks)

                        for disk in topdisks:
                            for i in self.processedData[stat]:
                                coltitle = i[:1][0]
                                for _ in fields:
                                    if coltitle == disk:
                                        read = np.array([float(x) for x in i[1:]])
                                        values.append((read, coltitle))

                    elif "all" in fields:
                        for i in self.processedData[stat]:
                            coltitle = i[:1][0]
                            for _ in fields:
                                if "hdisk" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))
                    else:
                        for i in self.processedData[stat]:
                            coltitle = i[:1][0]
                            for col in fields:
                                if coltitle == col:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "FCREAD" or stat == "FCWRITE" or stat == "FCXFERIN" or stat == "FCXFEROUT":
                log.debug("starting " + stat)
                if stat in self.processedData:
                    text = str(self.processedData[stat][0][0])
                    label = text.rpartition(' ')[0]

                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData[stat][0][1:]]
                    values = []

                    if times: # If only header exists in the NMON file, but no data.
                        if "all" in fields:
                            for i in self.processedData[stat]:
                                coltitle = i[:1][0]
                                for _ in fields:
                                    if "fcs" in coltitle:
                                        read = np.array([float(x) for x in i[1:]])
                                        values.append((read, coltitle))
                        else:
                            for i in self.processedData[stat]:
                                coltitle = i[:1][0]
                                for col in fields:
                                    if col in coltitle:
                                        read = np.array([float(x) for x in i[1:]])
                                        values.append((read, coltitle))

                        data = (times, values)
                        fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat, bar=True)
                        outfiles.append(fname)
                        fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat)
                        outfiles.append(fname)
                    else:
                        log.info(stat + " data does not exists in the nmon file!")
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "IOADAPT_R":
                log.debug("starting " + stat)
                if "IOADAPT" in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["IOADAPT"][0][1:]]

                    text = str(self.processedData["IOADAPT"][0][0])
                    label = text.rpartition(' ')[0]

                    values = []

                    if "all" in fields:
                        for i in self.processedData["IOADAPT"]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if "fcs" in coltitle and "read" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))
                                elif "vscsi" in coltitle and "read" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))
                                elif "sissas" in coltitle and "read" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                    else:
                        for i in self.processedData["IOADAPT"]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if iface in coltitle and "read" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat, bar=True)
                    outfiles.append(fname)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "IOADAPT_W":
                log.debug("starting " + stat)
                if "IOADAPT" in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["IOADAPT"][0][1:]]

                    text = str(self.processedData["IOADAPT"][0][0])
                    label = text.rpartition(' ')[0]

                    values = []

                    if "all" in fields:
                        for i in self.processedData["IOADAPT"]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if "fcs" in coltitle and "write" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))
                                elif "vscsi" in coltitle and "write" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))
                                elif "sissas" in coltitle and "write" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                    else:
                        for i in self.processedData["IOADAPT"]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if iface in coltitle and "write" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat, bar=True)
                    outfiles.append(fname)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "IOADAPT_XFER":
                log.debug("starting " + stat)
                if "IOADAPT" in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["IOADAPT"][0][1:]]

                    text = str(self.processedData["IOADAPT"][0][0])
                    label = text.rpartition(' ')[0]

                    values = []

                    if "all" in fields:
                        for i in self.processedData["IOADAPT"]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if "fcs" in coltitle and "xfer" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))
                                elif "vscsi" in coltitle and "xfer" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))
                                elif "sissas" in coltitle and "xfer" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                    else:
                        for i in self.processedData["IOADAPT"]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if iface in coltitle and "xfer" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))

                    data = (times, values)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat, bar=True)
                    outfiles.append(fname)
                    fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "NETPACKET" or stat == "NETSIZE":
                log.debug("starting " + stat)
                if stat in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData[stat][0][1:]]

                    text = str(self.processedData[stat][0][0])
                    label = text.rpartition(' ')[0]

                    values = []

                    if "all" in fields:
                        for i in self.processedData[stat]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if "en" in coltitle and "read" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                                elif "en" in coltitle and "write" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))

                    else:
                        for i in self.processedData[stat]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if iface in coltitle and "read" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                                elif iface in coltitle and "write" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))

                    data = (times, values)

                    if not values:
                        log.warning("Specified interface (" + iface + ") does not exists!")
                    else:
                        fname = self.plotstat(data, stat, xlabel="Time", ylabel=label, title=stat)
                        outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "MEMNEW":
                log.debug("starting " + stat)
                if stat in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["MEMNEW"][0][1:]]
                    values = [(self.processedData["MEMNEW"][3][1:], "system"),
                              (self.processedData["MEMNEW"][1][1:], "proc"),
                              (self.processedData["MEMNEW"][5][1:], "pinned"),
                              (self.processedData["MEMNEW"][6][1:], "user"),
                              (self.processedData["MEMNEW"][2][1:], "fscache"),
                              (self.processedData["MEMNEW"][4][1:], "free")]

                    data = (times, values)

                    fname = self.plotstat(data, stat, xlabel="Time", ylabel="Memory use (%)", title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "MEMUSE":
                log.debug("starting " + stat)
                if stat in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["MEMUSE"][0][1:]]
                    values = [(self.processedData["MEMUSE"][1][1:], "numperm"),
                              (self.processedData["MEMUSE"][2][1:], "minperm"),
                              (self.processedData["MEMUSE"][3][1:], "maxperm"),
                              (self.processedData["MEMUSE"][6][1:], "numclient"),
                              (self.processedData["MEMUSE"][7][1:], "maxclient")]

                    data = (times, values)

                    fname = self.plotstat(data, stat, xlabel="Time", ylabel="Memory tunables (%)", title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "PAGE":
                log.debug("starting " + stat)
                if stat in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["PAGE"][0][1:]]
                    values = [(self.processedData["PAGE"][1][1:], "faults"),
                              (self.processedData["PAGE"][2][1:], "pgin"),
                              (self.processedData["PAGE"][3][1:], "pgout"),
                              (self.processedData["PAGE"][4][1:], "pgsin"),
                              (self.processedData["PAGE"][5][1:], "pgsout")]

                    data = (times, values)

                    fname = self.plotstat(data, stat, xlabel="Time", ylabel="Paging", title=stat)
                    outfiles.append(fname)
                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")

            elif stat == "NET":
                log.debug("starting " + stat)
                if stat in self.processedData:
                    times = [datetime.datetime.strptime(d, "%d-%b-%Y %H:%M:%S") for d in
                             self.processedData["NET"][0][1:]]
                    values = []

                    if "all" in fields:
                        for i in self.processedData["NET"]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if "en" in coltitle and "read" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                                elif "en" in coltitle and "write" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))
                    else:
                        for i in self.processedData["NET"]:
                            coltitle = i[:1][0]
                            for iface in fields:
                                if iface in coltitle and "read" in coltitle:
                                    read = np.array([float(x) for x in i[1:]])
                                    values.append((read, coltitle))

                                elif iface in coltitle and "write" in coltitle:
                                    write = np.array([float(x) for x in i[1:]])
                                    values.append((write, coltitle))

                    data = (times, values)

                    if not values:
                        log.warning("Specified interface (" + iface + ") does not exists!")
                    else:
                        fname = self.plotstat(data, stat, xlabel="Time", ylabel="Network adapter", title=stat)
                        outfiles.append(fname)

                else:
                    log.info(stat + " data does not exists in the nmon file! Skipping..")
        return outfiles

    def plotstat(self, data, tab, xlabel="time", ylabel="", title="title", bar=False):

        # figure dimensions
        global yrange
        metric = ""

        fig = plt.figure(figsize=(13, 4), frameon=True)
        # resizing to hack the legend in the right location
        fig.subplots_adjust(right=.8)
        ax = fig.add_subplot(1, 1, 1)

        # retrieve timestamps and datapoints
        times, values = data

        if tab == "CPU_ALL":
            a = np.array([float(x) for x in values[0][0]])
            b = np.array([float(x) for x in values[1][0]])
            c = np.array([float(x) for x in values[2][0]])
            d = np.array([float(x) for x in values[3][0]])
            y = np.row_stack((a, b, c, d))
            y_ax = np.cumsum(y, axis=0)
            ax.fill_between(times, 0, y_ax[0, :], facecolor="green", label="usr")
            ax.fill_between(times, y_ax[0, :], y_ax[1, :], facecolor="red", label="sys")
            ax.fill_between(times, y_ax[1, :], y_ax[2, :], facecolor="blue", label="wait")
            ax.fill_between(times, y_ax[2, :], y_ax[3, :], facecolor="yellow", label="idle")

            # hack for getting around missing legend
            p1 = plt.Rectangle((0, 0), 1, 1, fc="g")
            p2 = plt.Rectangle((0, 0), 1, 1, fc="r")
            p3 = plt.Rectangle((0, 0), 1, 1, fc="b")
            p4 = plt.Rectangle((0, 0), 1, 1, fc="y")

            yrange = [0, 105]

            ax.legend([p1, p2, p3, p4], ["usr", "sys", "wait", "idle"], fancybox=True, loc='center left',
                      bbox_to_anchor=(1, 0.5))
            log.debug("Done plotting CPU_ALL graph")

        if tab == "PCPU_ALL":
            a = np.array([float(x) for x in values[0][0]])
            b = np.array([float(x) for x in values[1][0]])
            c = np.array([float(x) for x in values[2][0]])
            d = np.array([float(x) for x in values[3][0]])
            e = np.array([float(x) for x in values[4][0]])
            y = np.row_stack((a, b, c, d))
            y_ax = np.cumsum(y, axis=0)
            ax.fill_between(times, 0, y_ax[0, :], facecolor="green", label="usr")
            ax.fill_between(times, y_ax[0, :], y_ax[1, :], facecolor="red", label="sys")
            ax.fill_between(times, y_ax[1, :], y_ax[2, :], facecolor="blue", label="wait")
            ax.fill_between(times, y_ax[2, :], y_ax[3, :], facecolor="yellow", label="idle")

            ax.plot_date(times, e, "-", label="enc", color="magenta")

            # hack for getting around missing legend
            p1 = plt.Rectangle((0, 0), 1, 1, fc="g")
            p2 = plt.Rectangle((0, 0), 1, 1, fc="r")
            p3 = plt.Rectangle((0, 0), 1, 1, fc="b")
            p4 = plt.Rectangle((0, 0), 1, 1, fc="y")
            p5 = plt.Rectangle((0, 0), 1, 1, fc="m")

            yrange = [0, np.amax(y_ax) * 1.2]

            ax.legend([p1, p2, p3, p4, p5], ["usr", "sys", "wait", "idle", "enc = " + str(np.amax(e))], fancybox=True,
                      loc='center left', bbox_to_anchor=(1, 0.5))
            log.debug("Done plotting PCPU_ALL graph")

        elif tab == "LPAR":
            a = np.array([float(x) for x in values[0][0]])
            b = np.array([float(x) for x in values[1][0]])
            f = np.array([float(x) for x in values[2][0]])
            g = np.array([float(x) for x in values[3][0]])

            # Standard deviation calculation
            c = np.empty(a.size)
            a_std = np.std(a)
            c.fill(a_std)

            # Mean (average)
            e = np.empty(a.size)
            a_avg = np.mean(a)
            e.fill(a_avg)

            # Weighted average
            d = np.empty(a.size)
            sumprod = np.vdot(a, a)
            asum = a.sum()
            a_wa = sumprod / asum

            d.fill(a_wa)
            y = np.row_stack((a, b, f))

            ax.plot_date(times, y[0, :], "-", label="phyc", color="red")
            ax.plot_date(times, y[1, :], "-", label="enc", color="blue")
            ax.plot_date(times, c, "-", label="std dev", color="green")
            ax.plot_date(times, d, "-", label="wa", color="yellow")
            ax.plot_date(times, e, "-", label="avg", color="magenta")
            ax.plot_date(times, g, "-", label="VP", color="black")
            ax.plot_date(times, y[2, :], "-", label="folded VP", color="cyan")

            # hack for getting around missing legend
            p1 = plt.Rectangle((0, 0), 1, 1, fc="r")
            p2 = plt.Rectangle((0, 0), 1, 1, fc="b")
            p3 = plt.Rectangle((0, 0), 1, 1, fc="g")
            p4 = plt.Rectangle((0, 0), 1, 1, fc="y")
            p5 = plt.Rectangle((0, 0), 1, 1, fc="m")
            p6 = plt.Rectangle((0, 0), 1, 1, fc="c")  # folded VP
            p7 = plt.Rectangle((0, 0), 1, 1, fc="k")  # VP

            yrange = [0, (np.amax(g) * 1.2)]

            enc = "enc = " + str(np.amax(b))
            std_dev = "std dev = " + str("%.1f" % a_std)
            wa = "wa = " + str("%.1f" % a_wa)
            avg = "avg = " + str("%.1f" % a_avg)
            vp = "VP = " + str(np.amax(g))

            ax.legend([p1, p2, p3, p4, p5, p6, p7], ["phyc", enc, std_dev, wa, avg, "folded VP", vp], fancybox=True,
                      loc='center left', bbox_to_anchor=(1, 0.5))
            log.debug("Done plotting LPAR graph")

        elif tab == "POOL":
            a_neg = []

            a = np.array([float(x) for x in values[0][0]])  # PoolCPUs
            b = np.array([float(x) for x in values[1][0]])  # PoolIdle

            poolec = "PoolCPUs = " + str(np.amax(a))

            for i in range(0, len(a)):
                a_neg.append(np.amax(a) - b[i])

            y = np.row_stack((a, a_neg))

            ax.plot_date(times, y[0, :], "-", label="PoolCPUs", color="blue")
            ax.plot_date(times, y[1, :], "-", label="UsedPoolCPU", color="red")

            # hack for getting around missing legend
            p1 = plt.Rectangle((0, 0), 1, 1, fc="b")
            p2 = plt.Rectangle((0, 0), 1, 1, fc="r")

            yrange = [0, (np.amax(y) * 1.2)]

            ax.legend([p1, p2], [poolec, "UsedPoolCPU"], fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))
            log.debug("Done plotting POOL graph")

        elif tab == "PROC":
            a = np.array([float(x) for x in values[0][0]])  # Runnable
            b = np.array([float(x) for x in values[1][0]])  # Swap-in

            y = np.row_stack((a, b))

            ax.plot_date(times, y[0, :], "-", label="Runnable", color="blue")
            ax.plot_date(times, y[1, :], "-", label="Swap-in", color="red")

            # hack for getting around missing legend
            p1 = plt.Rectangle((0, 0), 1, 1, fc="b")
            p2 = plt.Rectangle((0, 0), 1, 1, fc="r")

            yrange = [0, (np.amax(y) * 1.2)]
            rq = "Runnable\n max = " + str(np.amax(a))

            ax.legend([p1, p2], [rq, "Swap-in"], fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))
            log.debug("Done plotting PROC graph")

        elif tab == "MEMNEW":
            a = np.array([float(x) for x in values[0][0]])  # system
            b = np.array([float(x) for x in values[1][0]])  # proc
            c = np.array([float(x) for x in values[2][0]])  # pinned
            d = np.array([float(x) for x in values[3][0]])  # user
            e = np.array([float(x) for x in values[4][0]])  # fscache
            f = np.array([float(x) for x in values[5][0]])  # free

            y = np.row_stack((a, b, e, f))
            y_ax = np.cumsum(y, axis=0)
            ax.fill_between(times, 0, y_ax[0, :], facecolor="green", label="system")
            ax.fill_between(times, y_ax[0, :], y_ax[1, :], facecolor="red", label="proc")
            ax.fill_between(times, y_ax[1, :], y_ax[2, :], facecolor="magenta", label="fscache")
            ax.fill_between(times, y_ax[2, :], y_ax[3, :], facecolor="cyan", label="free")

            ax.plot_date(times, c, "-", label="pinned", color="blue")
            ax.plot_date(times, d, "-", label="user", color="yellow")

            # hack for getting around missing legend
            p1 = plt.Rectangle((0, 0), 1, 1, fc="g")
            p2 = plt.Rectangle((0, 0), 1, 1, fc="r")
            p3 = plt.Rectangle((0, 0), 1, 1, fc="b")
            p4 = plt.Rectangle((0, 0), 1, 1, fc="y")
            p5 = plt.Rectangle((0, 0), 1, 1, fc="m")
            p6 = plt.Rectangle((0, 0), 1, 1, fc="c")

            yrange = [0, 105]

            ax.legend([p1, p2, p3, p4, p5, p6], ["system", "proc", "pinned", "user", "fscache", "free"], fancybox=True,
                      loc='center left', bbox_to_anchor=(1, 0.5))
            log.debug("Done plotting MEMNEW graph")

        elif tab == "MEMUSE":
            a = np.array([float(x) for x in values[0][0]])  # %numperm
            b = np.array([float(x) for x in values[1][0]])  # %minperm
            c = np.array([float(x) for x in values[2][0]])  # %maxperm
            d = np.array([float(x) for x in values[3][0]])  # %numclient
            e = np.array([float(x) for x in values[4][0]])  # %maxclient

            y = np.row_stack((a, b, c, d, e))

            ax.plot_date(times, y[0, :], "-", label="%numperm", color="red")
            ax.plot_date(times, y[1, :], "-", label="%minperm", color="blue")
            ax.plot_date(times, y[2, :], "-", label="%maxperm", color="green")
            ax.plot_date(times, y[3, :], "-", label="%numclient", color="yellow")
            ax.plot_date(times, y[4, :], "-", label="%maxclient", color="magenta")

            # hack for getting around missing legend
            p1 = plt.Rectangle((0, 0), 1, 1, fc="r")
            p2 = plt.Rectangle((0, 0), 1, 1, fc="b")
            p3 = plt.Rectangle((0, 0), 1, 1, fc="g")
            p4 = plt.Rectangle((0, 0), 1, 1, fc="y")
            p5 = plt.Rectangle((0, 0), 1, 1, fc="m")

            yrange = [0, 105]

            minperm = "%minperm = " + str("%.0f" % np.amax(b))
            maxperm = "%maxperm = " + str("%.0f" % np.amax(c))
            maxclient = "%maxclient = " + str("%.0f" % np.amax(e))

            ax.legend([p1, p2, p3, p4, p5], ["%numperm", minperm, maxperm, "%numclient", maxclient], fancybox=True,
                      loc='center left', bbox_to_anchor=(1, 0.5))
            log.debug("Done plotting MEMUSE graph")

        elif tab == "PAGE":
            a = np.array([float(x) for x in values[0][0]])  # faults
            b = np.array([float(x) for x in values[1][0]])  # pgin
            c = np.array([float(x) for x in values[2][0]])  # pgout
            d = np.array([float(x) for x in values[3][0]])  # pgsin
            e = np.array([float(x) for x in values[4][0]])  # pgsout

            y = np.row_stack((a, b, c, d, e))

            ax.plot_date(times, y[0, :], "-", label="faults", color="red")
            ax.plot_date(times, y[1, :], "-", label="pgin", color="blue")
            ax.plot_date(times, y[1, :], "-", label="pgout", color="green")
            ax.plot_date(times, y[1, :], "-", label="pgsin", color="yellow")
            ax.plot_date(times, y[1, :], "-", label="pgsout", color="cyan")

            # hack for getting around missing legend
            p1 = plt.Rectangle((0, 0), 1, 1, fc="r")
            p2 = plt.Rectangle((0, 0), 1, 1, fc="b")
            p3 = plt.Rectangle((0, 0), 1, 1, fc="g")
            p4 = plt.Rectangle((0, 0), 1, 1, fc="y")
            p5 = plt.Rectangle((0, 0), 1, 1, fc="c")

            yrange = [0, (np.amax(y) * 1.2)]

            ax.legend([p1, p2, p3, p4, p5], ["faults", "pgin", "pgout", "pgsin", "pgsout"], fancybox=True,
                      loc='center left', bbox_to_anchor=(1, 0.5))
            log.debug("Done plotting PAGE graph")

        elif tab == "DISKBUSY" or tab == "DISKREAD" or tab == "DISKWRITE" or tab == "DISKREADSERV" or tab == "DISKWRITESERV" or tab == "DISKRIO" or tab == "DISKWIO" or tab == "DISKRXFER" or tab == "DISKXFER" or tab == "DISKWAIT" or tab == "DISKBSIZE":
            maxdata = []
            for v, label in values:
                mx = np.amax(v)
                l = label + "\n max: " + format(mx, '0,.1f')
                ax.plot_date(times, v, "-", label=l)
                maxdata.append(mx)

            ax.legend(fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))

            if tab == "DISKBUSY":
                yrange = [0, 105]
            else:
                yrange = [0, (np.amax(maxdata) * 1.2)]

            log.debug("Done plotting " + tab + " graph")

        elif tab == "FCREAD" or tab == "FCWRITE" or tab == "FCXFERIN" or tab == "FCXFEROUT":
            mx = []
            if tab == "FCREAD" or tab == "FCWRITE":
                metric = "KB/s"
            else:
                metric = "IOPS"
            if bar: # plot bar charts
                avg = []
                wa = []
                width = 0.1
                l = []
                labels = []

                for v, label in values:
                    mx.append(np.amax(v))
                    avg.append(np.mean(v))
                    labels.append(label)
                    sumprod = np.vdot(v, v)
                    asum = v.sum()
                    wa.append(sumprod / asum)

                p1 = plt.Rectangle((0, 0), 1, 1, fc="g")
                p2 = plt.Rectangle((0, 0), 1, 1, fc="b")
                p3 = plt.Rectangle((0, 0), 1, 1, fc="r")

                index = np.arange(len(labels))
                ax.bar(index, mx, width, color='g', align='center')
                ax.bar(index + width, avg, width, color='b', align='center')
                ax.bar(index + width + width, wa, width, color='r', align='center')
                ax.set_xticks(index + width)
                ax.set_xticklabels(labels)

                ax.legend([p1, p2, p3], ["Maximum", "Average", "Weighted Average"], fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))

                yrange = [0, (np.amax(mx) * 1.2)]

                log.debug("Done plotting " + tab + " graph - BAR")
            else: # plot line chart
                for v, label in values:
                    l = label + "\n max: " + format(np.amax(v), '0,.1f')
                    ax.plot_date(times, v, "-", label=l)
                    mx.append(np.amax(v))

                ax.legend(fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))

                yrange = [0, (np.amax(mx) * 1.2)]

                log.debug("Done plotting " + tab + " graph - LINE")

        elif tab == "NET" or tab == "NETPACKET" or tab == "NETSIZE":
            maxdata = []
            for v, label in values:
                mx = np.amax(v)
                l = label + "\n max: " + format(mx, '0,.1f')
                ax.plot_date(times, v, "-", label=l)
                maxdata.append(mx)

            ax.legend(fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))

            yrange = [0, (np.amax(maxdata) * 1.2)]

            log.debug("Done plotting " + tab + " graph")

        elif tab == "IOADAPT_R" or tab == "IOADAPT_W" or tab == "IOADAPT_XFER":
            mx = []
            if bar: # plot bar charts
                avg = []
                wa = []
                width = 0.1
                l = []
                labels = []

                for v, label in values:
                    mx.append(np.amax(v))
                    avg.append(np.mean(v))
                    l.append(label)
                    sumprod = np.vdot(v, v)
                    asum = v.sum()
                    wa.append(sumprod / asum)

                for i in l:
                    bits = i.split('_')
                    labels.append(bits[0])
                    metric = bits[1]

                p1 = plt.Rectangle((0, 0), 1, 1, fc="g")
                p2 = plt.Rectangle((0, 0), 1, 1, fc="b")
                p3 = plt.Rectangle((0, 0), 1, 1, fc="r")

                index = np.arange(len(labels))
                ax.bar(index, mx, width, color='g', align='center')
                ax.bar(index + width, avg, width, color='b', align='center')
                ax.bar(index + width + width, wa, width, color='r', align='center')
                ax.set_xticks(index + width)
                ax.set_xticklabels(labels)

                ax.legend([p1, p2, p3], ["Maximum", "Average", "Weighted Average"], fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))

                yrange = [0, (np.amax(mx) * 1.2)]

                log.debug("Done plotting " + tab + " graph - BAR")
            else: # plot line chart
                for v, label in values:
                    bits = label.split('_')
                    metric = bits[1]

                    l = label + "\n max: " + format(np.amax(v), '0,.1f')
                    ax.plot_date(times, v, "-", label=l)
                    mx.append(np.amax(v))

                ax.legend(fancybox=True, loc='center left', bbox_to_anchor=(1, 0.5))

                yrange = [0, (np.amax(mx) * 1.2)]

                log.debug("Done plotting " + tab + " graph - LINE")

        # format axis
        if not bar:
            # ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(10))
            ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b.%d. %H:%M"))
            # ax.xaxis.set_minor_locator(mpl.ticker.MaxNLocator(100))

            ax.autoscale_view()

            ax.set_ylim(yrange)
            ax.grid(which='major', color='k', linestyle=':', linewidth=1)

            fig.autofmt_xdate()

            ax.set_ylabel(ylabel + " " + metric)
            ax.set_xlabel(xlabel)

            outfilename = os.path.join(self.imgPath, title.replace(" ", "_") + ".png")

        else:
            ax.autoscale_view()

            ax.set_ylim(yrange)
            ax.grid(which='major', color='k', linestyle=':', linewidth=1)
            ax.set_ylabel(ylabel + " " + metric)

            outfilename = os.path.join(self.imgPath, title.replace(" ", "_") + "_bar.png")
        hname = ""

        for i in sysInfo:
            if i[0] == "host":
                hname = i[1]

        ax.set_title(hname + " - " + tab, size=16, weight='bold')

        plt.savefig(outfilename)
        plt.close()
        return outfilename


#
# Data file parsing
#

class Pynmonparser:
    fname = ""
    dname = ""
    outdir = ""

    # Holds final 2D arrays of each stat
    processedData = {}
    # Holds System Info gathered by nmon
    bbbInfo = []
    # Holds timestamps for later lookup
    tStamp = {}

    def __init__(self, fname="", dname="", outdir="", debug=False):
        self.fname = fname
        self.dname = dname
        self.outdir = outdir
        self.debug = debug

    def outputcsv(self, stat):
        outfile = open(os.path.join(self.outdir, stat + ".csv"), "w")
        if len(self.processedData[stat]) > 0:
            # Iterate over each row
            for n in range(len(self.processedData[stat][0])):
                line = ""
                # Iterate over each column
                for col in self.processedData[stat]:
                    if line == "":
                        # expecting first column to be date times
                        if n == 0:
                            # skip headings
                            line += col[n]
                        else:
                            tstamp = datetime.datetime.strptime(col[n], "%d-%b-%Y %H:%M:%S")
                            line += tstamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        line += "," + col[n]
                outfile.write(line + "\n")

    def processline(self, header, line):
        if "AAA" in header:
            # we are looking at the basic System Specs
            sysInfo.append(line[1:])
        elif "BBB" in header:
            # more detailed System Spec
            # do more granular processing
            # refer to pg 11 of analyzer handbook
            self.bbbInfo.append(line)
        elif "ZZZZ" in header:
            self.tStamp[line[1]] = line[3] + " " + line[2]
        else:
            if "TOP" in line[0] and len(line) > 3:
                # top lines are the only ones that do not have the timestamp
                # as the second column, therefore we rearrange for parsing.
                # kind of a hack, but so is the rest of this parsing
                pid = line[1]
                line[1] = line[2]
                line[2] = pid

            if line[0] in list(self.processedData.keys()):
                table = self.processedData[line[0]]
                for n, col in enumerate(table):
                    # line[1] give you the T####
                    if n == 0 and line[n + 1] in list(self.tStamp.keys()):
                        # lookup the time stamp in tStamp
                        col.append(self.tStamp[line[n + 1]])

                    elif n == 0 and line[n + 1] not in list(self.tStamp.keys()):
                        # log.warn("Discarding line with missing Timestamp %s" % line)
                        break

                    else:
                        if len(line) > n + 1:
                            col.append(line[n + 1])
                        else:
                            # somehow we are missing an entry here
                            # As in we have a heading, but no data
                            col.append("0")
                            # this should always be a float
                            # try:
                            #       col.append(float(line[n+1]))
                            # except:
                            #       print line[n+1]
                            #       col.append(line[n+1])

            else:
                # new column, hoping these are headers
                # We are expecting a header row like:
                # CPU01,CPU 1 the-gibson,User%,Sys%,Wait%,Idle%
                header = []
                if "TOP" in line[0] and len(line) < 3:
                    # For some reason Top has two header rows, the first with only
                    # two columns and then the real one therefore we skip the first row
                    pass
                else:
                    for h in line[1:]:
                        # make it an array
                        tmp = [h]
                        header.append(tmp)
                    self.processedData[line[0]] = header

    def parse(self):
        if self.fname:
            f = open(self.fname, "r")
            log.info("Reading and parsing: " + self.fname)
            rawdata = f.readlines()
            for l in rawdata:
                l = l.strip()
                bits = l.split(',')
                self.processline(bits[0], bits)
        # Merging files
        elif self.dname:
            log.info("Reading files from: " + self.dname)
            path = os.path.join(self.dname, "*.nmon")

            # Cleanup
            if not os.path.exists("./temp"):
                os.makedirs("./temp")

            if os.path.exists("./temp/merged.nmon"):
                os.remove("./temp/merged.nmon")

            mergedfile = os.path.join("temp/merged.nmon")
            files = glob.glob(path)

            # Sorting file
            files.sort()

            log.debug("Merging NMON files")
            log.debug(files)

            s = set()

            with open(mergedfile, 'w') as outfile:
                for fname in files:
                    log.info("Merging: " + fname)
                    with open(fname) as infile:
                        for line in infile:
                            linestr = str(line)
                            # Make AAA lines unique
                            if linestr.startswith("AAA") and line not in s:
                                outfile.write(line)
                                s.add(line)
                            elif not linestr.startswith("AAA"):
                                outfile.write(line)
            log.debug("Done merging")

            f = open(mergedfile, "r")
            log.info("Reading and parsing: " + mergedfile)
            rawdata = f.readlines()
            for l in rawdata:
                l = l.strip()
                bits = l.split(',')
                self.processline(bits[0], bits)

        return self.processedData

    def output(self, outtype="csv"):

        if len(self.processedData) <= 0:
            # nothing has been parsed yet
            log.error("Output called before parsing")
            exit()

        # make output dir
        self.outdir = os.path.join(self.outdir, outtype)
        if not (os.path.exists(self.outdir)):
            try:
                os.makedirs(self.outdir)
            except:
                log.error("Creating results dir:", self.outdir)
                exit()

        # switch for different output types
        if outtype.lower() == "csv":
            # Write out to multiple CSV files
            for l in list(self.processedData.keys()):
                self.outputcsv(l)
        else:
            log.error("Output type has not been implemented: " + outtype)
            exit()


#
# Main function
#

class Pynmongraph:
    # Holds final 2D arrays of each stat
    processedData = {}
    nmonParser = None

    # Fix logging
    log.getLogger('').handlers = []

    # Holds System Info gathered by nmon
    bbbInfo = []
    args = []

    def __init__(self, args=None, raw_args=None):
        if args is None and raw_args is None:
            log.error("args and rawargs cannot be None.")
            sys.exit()
        if args is None:
            self.args = self.parseargs(raw_args)
        else:
            self.args = args

        if self.args.buildreport:
            # check whether specified report config exists
            if not os.path.exists(self.args.confFname):
                log.warn("looks like the specified config file(\"" + self.args.confFname + "\") does not exist.")

                sys.exit()

        # check for Python version
        pyversion = platform.python_version()
        log.info("Python " + pyversion)
        
        # check ouput dir, if not create
        if os.path.exists(self.args.outdir) and self.args.overwrite:
            try:
                rmtree(self.args.outdir)
                log.info("Removing old dir..")
            except:
                log.error("Removing old dir:", self.args.outdir)
                sys.exit()

        elif os.path.exists(self.args.outdir):
            log.error("Results directory already exists, please remove or use '-x' to overwrite")
            sys.exit()

        # This is where the magic begins
        self.nmonParser = Pynmonparser(self.args.input_file, self.args.input_dir, self.args.outdir)
        self.processedData = self.nmonParser.parse()

        if self.args.outputcsv:
            log.info("Preparing CSV files..")
            self.outputdata("csv")



        if self.args.buildreport:
            log.info("Preparing html Report..")
            self.buildreport()
        else:
            log.info("Not creating report..")

        log.info("All done, exiting.")

    @staticmethod
    def parseargs(raw_args):
        parser = argparse.ArgumentParser(
            description="nmonParser converts NMON monitor files into time-sorted CSV/Spreadsheets for easier analysis, without the use of the MS Excel Macro. Also included is an option to build an HTML report with graphs, which is configured through report.config.")
        parser.add_argument("-x", "--overwrite", action="store_true", dest="overwrite",
                            help="overwrite existing results (Default: False)")
        parser.add_argument("-d", "--debug", action="store_true", dest="debug", help="debug? (Default: False)")
        parser.add_argument("--force", action="store_true", dest="force", help="force using of config (Default: False)")
        parser.add_argument("-i", "--inputfile", dest="input_file", default="", help="Input NMON file")
        parser.add_argument("-I", "--inputdir", dest="input_dir", default="./nmon/",
                            help="Input directory with multiple NMON file")
        parser.add_argument("-o", "--output", dest="outdir", default="./report/",
                            help="Output dir for CSV (Default: ./report/)")
        parser.add_argument("-c", "--csv", action="store_true", dest="outputcsv", help="CSV output? (Default: False)")
        parser.add_argument("-b", "--buildreport", action="store_true", dest="buildreport",
                            help="report output? (Default: False)")
        parser.add_argument("-r", "--reportconfig", dest="confFname", default="./report.config",
                            help="Report config file. Default is ./report.config")
        args = parser.parse_args(raw_args)

        if len(sys.argv) == 1:
            # no arguments specified
            parser.print_help()
            sys.exit()

        if args.debug:
            log.basicConfig(level=10, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
        else:
            log.basicConfig(level=20, format='%(levelname)s - %(message)s')

        return args

    def loadreportconfig(self, configfname="report.config"):
        f = open(configfname, "r")
        reportconfig = []

        # loop over all lines
        for l in f:
            l = l.strip()
            fields = []
            # ignore lines beginning with #
            if l[0:1] != "#":
                bits = l.split("=")

                # check whether we have the right number of elements
                if len(bits) == 2:
                    optstart = -1

                    stat = bits[0]
                    if bits[1] != "":
                        if optstart != -1:
                            fields = bits[1][:optstart - 1].split(",")
                        else:
                            fields = bits[1].split(",")

                    if self.args.debug:
                        log.debug("%s %s" % (stat, fields))

                    # add to config
                    reportconfig.append((stat, fields))

        f.close()
        return reportconfig

    def buildreport(self):
        global runtime

        nmonplotter = Pynmonplotter(self.processedData, self.args.outdir, debug=self.args.debug)

        # Note: CPU and MEM both have different logic currently, so they are just handed empty arrays []
        #       For DISKBUSY and NET please do adjust the columns you'd like to plot

        if os.path.exists(self.args.confFname):
            reportconfig = self.loadreportconfig(configfname=self.args.confFname)
        else:
            log.error("something went wrong.. looks like %s is missing. run --defaultConfig to generate a template" % (
                self.args.confFname))
            sys.exit()

        outfiles = nmonplotter.plotstats(reportconfig)

        stop = timeit.default_timer()

        runtime = stop - start
        log.info("Running time: " + str("%.1f" % runtime) + " seconds")

        # Build HTML report
        createreport(outfiles, self.args.outdir)

    def outputdata(self, outputFormat):
        self.nmonParser.output(outputFormat)


if __name__ == "__main__":
    _ = Pynmongraph(raw_args=sys.argv[1:])
