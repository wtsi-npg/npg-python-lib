# -*- coding: utf-8 -*-
#
# Copyright © 2024 Genome Research Ltd. All rights reserved.
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


from pytest import mark as m

from npg.iter import with_previous


@m.describe("with_previous")
class TestWithPrevious:
    @m.it("Returns pairs of previous and current items")
    def test_returns_pairs_of_previous_and_current_items(self):
        result = list(with_previous([1, 2, 3]))
        expected = [(None, 1), (1, 2), (2, 3), (3, None)]
        assert result == expected

    @m.it("Handles an empty iterable")
    def test_handles_empty_iterable(self):
        result = list(with_previous([]))
        expected = [(None, None)]
        assert result == expected

    @m.it("Handles a single element iterable")
    def test_handles_single_element_iterable(self):
        result = list(with_previous([1]))
        expected = [(None, 1), (1, None)]
        assert result == expected

    @m.it("Handles an iterable with None")
    def test_handles_iterable_with_none(self):
        result = list(with_previous([None, 1, None]))
        expected = [(None, None), (None, 1), (1, None), (None, None)]
        assert result == expected
