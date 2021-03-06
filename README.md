# autotable

autotable is a procedural timetable generator for the free
[Open Rails](http://openrails.org) train simulator. It uses
[General Transit Feed Specification](https://developers.google.com/transit)
data to recreate real-life schedules.

![Console screenshot](https://raw.githubusercontent.com/wiki/yoryan/autotable/demo_console.jpg)

![Timetable CSV screenshot](https://raw.githubusercontent.com/wiki/yoryan/autotable/demo_csv.jpg)

As a timetable designer, you configure autotable through an easy-to-read YAML
recipe file that defines the consist, path, and other control commands for each
run. Since GTFS was intended for passenger wayfinding and not dispatch or
operations planning, it is still your responsibility to mock up paths, assign
platforms, and define rolling stock. But by sourcing data from GTFS feeds,
autotable automates away the rote work of copying and pasting (or manually
entering) individual arrival and departure times.

autotable also makes it easy to swap in your own equipment - just change out
the `consist` fields - if you use a timetable recipe made by somebody else.

autotable is a command-line tool written in Python 3. It uses
[GTFS Kit](https://github.com/mrcagney/gtfs_kit) to parse GTFS feeds, and an
internal reader to parse Microsoft Train Simulator/Open Rails data files.

### Quick start

#### Download autotable

You'll find ready-to-run executables on the
[releases](https://github.com/YoRyan/autotable/releases) page.

(I apologize for the large package size. The program itself is quite small, but
the supporting libraries and geographic data take up several hundred more
megabytes of space.)

#### Usage

autotable is a command-line program.

```
>autotable --help
usage: autotable [-h] msts yaml

Generate Open Rails timetables from GTFS data.

positional arguments:
  msts        path to MSTS installation or mini-route
  yaml        path to timetable recipe file

optional arguments:
  -h, --help  show this help message and exit
```

The final timetable is written as a `.timetable-or` file with the same basename
and parent directory as the recipe file.

#### Install from source

As of February 2020, some of the PyPI dependencies will not build and install on
Windows. You can get prebuilt wheels (install them in the listed order) courtesy
of [Christoph Gohlke](https://www.lfd.uci.edu/~gohlke/pythonlibs/):

1. [GDAL](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)
2. [Fiona](https://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona)
3. [rtree](https://www.lfd.uci.edu/~gohlke/pythonlibs/#rtree)

Then, to install autotable:

```
>pip install git+https://github.com/YoRyan/autotable
```

I use [cx_Freeze](https://anthony-tuininga.github.io/cx_Freeze/) to build
redistributable Windows executables. If you wish to produce your own build, run:

```
>python setup_exe.py build
```

### Recipe files

Timetable recipes are YAML files that select trips from GTFS files and apply
properties and control commands. Some example recipes are available in the
[samples/](samples/) directory.

```
route: SOME_ROUTE
date: 2020-01-01
gtfs:
  - file: path/to/my/gtfs.zip
    groups:
      - selection:
            trip_short_name: '^your regex here$'
        path: some path
        consist: some consist
        start_time: -MM:SS
        speed_mph: ''
        delay: ''
        note: ''
        dispose: ''
    station_map:
        stop id: Station Name
    station_commands:
        station name: ''
```

(Unfortunately, the Open Rails manual does not yet document all available
commands. Refer to the May 2017 timetable
[design document](http://www.elvastower.com/forums/index.php?/topic/30326-update-timetable-mode-signalling/).)

Recipes should be YAML dictionaries with the following keys:

#### route

The name of the route's directory in ROUTES\\.

#### date

Select trips that overlap this date. Take care that your GTFS feeds are in
service on this date. Must be in ISO 8601 format so that it is readable by
PyYAML.

#### timezone

*Default: timezone at route origin*

Set the timezone all times in the timetable will be in reference to. Open Rails
has no concept of timezones, so whichever timezone you define will apply to all
trains at all times, regardless of their current positions.

You would want to set this if you expect the majority of your operations to
occur in a timezone different from the one implied by the route's start tile.
Use a standardized timezone name for this field, like `America/Los_Angeles` or
`America/New_York`.

#### speed_unit

*Default: m/s*

Open Rails does not allow the use of multiple `#speed` rows in a single timetable.
This means that all *speed* commands must use the same unit of measure. Specify one
of the following here:

- `ms`
- `kph`
- `mph`

If you are not using any *speed* commands, this option has no effect.

#### gtfs

A list of dictionaries representing the GTFS sources and their trips. A single
timetable can source from multiple GTFS files. Each gtfs block must specify a
`file` or `url` but not both.

##### file

Load a GTFS file from the local filesystem. The path is relative to the current
directory.

##### url

Load a GTFS file from the Internet. Must be a full HTTP or HTTPS URL.

##### groups

A list of dictionaries representing groups of trips. Groups apply a path,
consist, and other attributes to a particular subset of GTFS trips.

Groups are processed first-to-last and can override previously defined
attributes, so you can add smaller groups to fine-tune previously
included trips.

Trips will not be written to the timetable unless assigned both a consist
and path. Of course, they must also make at least one stop at a station
represented by the route.

###### selection

A dictionary that selects trips by their attributes as defined in
[the GTFS spec](https://developers.google.com/transit/gtfs/reference#tripstxt).
Each key represents an attribute name, and the corresponding value
represents a regular expression to match attribute values.

Multiple filtered attributes are applied in an AND relationship.

###### path

The filename of the trips' path, without the .pat extension.

###### consist

The filename of trips' consist, without the .con extension, OR a list of
consist filenames without the .con extensions, which will be combined into a
single train in-game.

You may also append a ` $reverse` flag after the name of a consist to reverse
its direction.

###### start

Set the *start* commands that apply when the trips spawn.

###### start_time

*Default: 120 seconds before*

Set trip spawn times relative to their arrival times at their first on-route
stops.

Negative values push the start time back, while positive values move it forward
(thus spawning a "late" train).

You will want to adjust this based on the distance between the path's start
node and its first stop.

###### note

Set *train* commands. The Open Rails manual
[suggests](https://open-rails.readthedocs.io/en/stable/timetable.html#special-rows)
using `$dec=2` or `$dec=3` for modern equipment.

###### speed

Set *speed* commands. All commands must use the same unit of measure, which is
defined by the top-level `speed_unit` directive.

###### delay

Set the *restart delay* commands that control fixed and random delays over the
course of the trips.

###### dispose

Set the *dispose* commands that apply when the trips terminate at their last
represented stations.

###### station_commands

A dictionary that maps in-game station names to *station stop* commands.

###### station_map

This is equivalent to the `station_map` field of the `gtfs` block (below),
except that it applies only to trips selected by this `groups` block.

##### station_map

A dictionary that maps GTFS `stop_id`'s to their corresponding in-game station
names.

autotable tries to build this automatically by first filtering all platforms
within a 10km radius (to account for route-building inaccuracies) and then
looking for words that are common to both the GTFS and in-game names. Usually,
this heuristic gets it right, but you can fine-tune the results by adding
mappings here, which will override the automatic ones.

As a debugging aid, when autotable writes the final timetable, it adds a
`#comment` row beneath every station that contains the GTFS stop(s) that were
mapped to it.

Specify a blank station name to denote a GTFS stop that explicitly has no
in-game equivalent, to resolve ambiguous cases where the same stop apparently
maps to multiple stations.

#### station_commands

A dictionary that maps in-game station names to *station* commands.

The special empty key `""` applies to all stations that do not have commands
specifically defined for themselves.

(Protip: Route builders often forget to change the minimum platform wait time
from the MSTS-default 3 minutes, so use the `$stoptime=s` command to specify
your own.)
