# coding: utf-8
#
# ubirch anchoring test
#
# @author Victor Patrin
#
# Copyright (c) 2018 ubirch GmbH.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ubirch.anchoring import *
import unittest

# TODO : add more tests


class TestUbirchAnchoring(unittest.TestCase):

    def test_is_hex(self):
        lowerhex = "0x0123456789abcdef"
        upperhex = "0xABCDEF"
        nonhex = "0x123helloworld"
        self.assertTrue(is_hex(lowerhex))
        self.assertTrue(is_hex(upperhex))
        self.assertTrue(not(is_hex(nonhex)))







