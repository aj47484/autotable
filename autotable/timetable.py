# -*- coding: utf-8 -*-
import csv
import datetime as dt
import re
import typing as typ
from dataclasses import dataclass
from enum import Enum
from functools import reduce

from more_itertools import pairwise, quantify

from autotable.mstsinstall import Consist, Route, Station


@dataclass
class Stop:
    station: Station
    comment: str
    arrival: dt.datetime
    departure: dt.datetime


@dataclass
class ConsistComponent:
    consist: Consist
    reverse: bool

    def __str__(self) -> str:
        if re.search(r'[\+\$]', self.consist.id):
            if self.reverse:
                return f'<{self.consist.id}>$reverse'
            else:
                return f'<{self.consist.id}>'
        elif self.reverse:
            return f'{self.consist.id} $reverse'
        else:
            return self.consist.id


@dataclass
class Trip:
    name: str
    stops: typ.Sequence[Stop]
    path: Route.TrainPath
    consist: typ.Sequence[ConsistComponent]
    start_offset: int
    start_commands: str
    note_commands: str
    speed_commands: str
    delay_commands: str
    station_commands: typ.Mapping[Station, str]
    dispose_commands: str

    def start_time(self) -> dt.datetime:
        first_stop = self.stops[0].arrival
        return first_stop + dt.timedelta(seconds=self.start_offset)


class SpeedUnit(Enum):
    MS = 1
    KPH = 2
    MPH = 3


@dataclass
class Timetable:
    name: str
    route: Route
    date: dt.date
    tzinfo: dt.tzinfo
    trips: typ.Sequence[Trip]
    station_commands: typ.Mapping[Station, str]
    speed_unit: SpeedUnit

    def write_csv(self, fp: typ.TextIO) -> None:
        # csv settings per the May 2017 timetable document
        # http://www.elvastower.com/forums/index.php?/topic/30326-update-timetable-mode-signalling/
        writer = csv.writer(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        def writerow(*args) -> None: writer.writerow(args)

        def strftime(dt: dt.datetime) -> str:
            return dt.astimezone(self.tzinfo).strftime('%H:%M')

        ordered_stations = _order_stations(self.trips)
        ordered_trips = self.trips

        writerow('', '', '#comment', *(trip.name for trip in ordered_trips))
        writerow('#comment', '', self.name)
        writerow('#path', '', '', *(trip.path.id for trip in ordered_trips))

        def consist_col(trip: Trip) -> str:
            return '+'.join(str(subconsist) for subconsist in trip.consist)
        writerow('#consist', '', '', *(consist_col(trip) for trip in ordered_trips))

        def start_col(trip: Trip) -> str:
            if trip.start_commands:
                return f'{strftime(trip.start_time())} {trip.start_commands}'
            else:
                return strftime(trip.start_time())
        writerow('#start', '', '', *(start_col(trip) for trip in ordered_trips))

        writerow('#note', '', '', *(trip.note_commands for trip in ordered_trips))

        speed_commands = (trip.speed_commands for trip in ordered_trips)
        if self.speed_unit == SpeedUnit.MS:
            writerow('#speed', '', '', *speed_commands)
        elif self.speed_unit == SpeedUnit.KPH:
            writerow('#speedkph', '', '', *speed_commands)
        elif self.speed_unit == SpeedUnit.MPH:
            writerow('#speedmph', '', '', *speed_commands)

        writerow('#restartdelay', '', '',
                 *(trip.delay_commands for trip in ordered_trips))

        stops_index = {}
        for i, trip in enumerate(ordered_trips):
            for stop in trip.stops:
                stops_index[(i, stop.station)] = stop

        def station_stops(s_name: str) -> typ.Generator[str, None, None]:
            for i, trip in enumerate(ordered_trips):
                stop = stops_index.get((i, s_name), None)
                if stop is None:
                    yield ''
                    continue

                if (stop.arrival.hour == stop.departure.hour
                        and stop.arrival.minute == stop.departure.minute):
                    time = strftime(stop.arrival)
                else:
                    time = f'{strftime(stop.arrival)}-{strftime(stop.departure)}'

                commands = trip.station_commands.get(s_name,
                    trip.station_commands.get('', ''))
                yield f'{time} {commands}' if commands else time

        def station_comments(s_name: str) -> typ.Generator[str, None, None]:
            for i, _ in enumerate(ordered_trips):
                stop = stops_index.get((i, s_name), None)
                yield stop.comment if stop is not None else ''

        writerow()
        for s_name in ordered_stations:
            commands = self.station_commands.get(
                s_name, self.station_commands.get('', ''))
            writerow(s_name, commands, '', *station_stops(s_name))
            writerow('#comment', '', '', *station_comments(s_name))
        writerow()

        writerow('#dispose', '', '',
                 *(trip.dispose_commands for trip in ordered_trips))


def _order_stations(trips: typ.Iterable[Trip]) -> typ.Sequence[Station]:
    # This greedy algorithm sometimes gets the order wrong, but it's fast.
    def add_trip(current_order: typ.Sequence[Station], trip: Trip) \
            -> typ.Sequence[Station]:
        def merge_in(order: typ.Iterable[Station]) -> typ.List[Station]:
            return list(merge_inb(order))

        current_idx = {station: i for i, station in enumerate(current_order)}
        def merge_inb(order: typ.Iterable[Station]) \
                -> typ.Generator[Station, None, None]:
            ptr = 0
            for station in order:
                if station in current_idx:
                    newptr = max(ptr, current_idx[station] + 1)
                    yield from current_order[ptr:newptr]
                    ptr = newptr
                else:
                    yield station
            yield from current_order[ptr:]

        def score(order: typ.Iterable[Station],
                  compare_to: typ.Iterable[Station]) -> int:
            idx = {station: i for i, station in enumerate(order)}
            return quantify(idx[s1] < idx[s2] for s1, s2
                            in pairwise(compare_to))

        fwd_order = tuple(stop.station for stop in trip.stops)
        fwd_merged = merge_in(fwd_order)
        bwd_order = tuple(reversed(fwd_order))
        bwd_merged = merge_in(bwd_order)
        return (fwd_merged
                if score(fwd_merged, fwd_order) >= score(bwd_merged, bwd_order)
                else bwd_merged)

    return reduce(add_trip, trips, [])
