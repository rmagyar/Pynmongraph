PyNmonGraph
========

Python based NMON analyzer tool based on pyNmonAnalyzer (https://github.com/madmaze/pyNmonAnalyzer)

The goal of this tool is to provide the same (or even more) features as the Excel based nmon_analyzer tool with the following benefits:

- Platform independent 
- Single Python script
- Ability to parse and analyze huge (more than 100MB size nmon files)
- Static HTML report
- CSV generation for further tooling
- Advanced metrics, such as standard deviation and weighted average
- More to come...

Dependencies:  
-----
This tool depends on the python numpy package and the matplotlib package and Python 2.7
* If you are on a Debian/Ubuntu based system: `sudo apt-get install python-numpy python-matplotlib`  
* If you are on a RHEL/Fedora/Centos system: `sudo yum install python-numpy python-matplotlib`
* If you are on Windows: Install Anaconda (https://www.continuum.io/downloads) as it has all the required modules

Usage:
-----
```
usage: pyNmonGraph.py [-h] [-x] [-d] [--force] [-i INPUT_FILE] [-I INPUT_DIR]
                      [-o OUTDIR] [-c] [-b] [-r CONFFNAME]

nmonParser converts NMON monitor files into time-sorted CSV/Spreadsheets for
easier analysis, without the use of the MS Excel Macro. Also included is an
option to build an HTML report with graphs, which is configured through
report.config.

optional arguments:
  -h, --help            show this help message and exit
  -x, --overwrite       overwrite existing results (Default: False)
  -d, --debug           debug? (Default: False)
  --force               force using of config (Default: False)
  -i INPUT_FILE, --inputfile INPUT_FILE
                        Input NMON file
  -I INPUT_DIR, --inputdir INPUT_DIR
                        Input directory with multiple NMON file
  -o OUTDIR, --output OUTDIR
                        Output dir for CSV (Default: ./report/)
  -c, --csv             CSV output? (Default: False)
  -b, --buildReport     report output? (Default: False)
  -r CONFFNAME, --reportConfig CONFFNAME
                        Report config file. Default is ./report.config

```                   

License:
-------
```
Copyright (c) 2015 Richard Magyar, rmagyar78[]gmail.com
Copyright (c) 2012-2015 Matthias Lee, matthias.a.lee[]gmail.com
Last edited: October 25th 2015

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
```