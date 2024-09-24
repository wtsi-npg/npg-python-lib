# -*- coding: utf-8 -*-
#
# Copyright © 2023 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import itertools
from typing import Iterable


def with_previous(iterable: Iterable) -> Iterable:
    """Return an iterable that yields pairs of items from the argument iterable, each
    pair consisting of the previous item and the current item. The first tuple contains
    a pair of None and the first item, the last tuple contains the pair of the last item
    and None. e.g.

        [x for x in with_previous(range(3)] => [(None, 1), (1, 2), (2, None)]

    Args:
        iterable: An iterable to wrap.

    Returns:
        An iterable of tuples.
    """
    lead, lag = itertools.tee(iterable, 2)
    return itertools.zip_longest(
        itertools.chain(iter([None]), lead), lag, fillvalue=None
    )
