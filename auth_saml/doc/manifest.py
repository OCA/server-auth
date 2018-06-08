#!/usr/bin/env python3
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016, 2018 XCG Consulting (http://www.xcg-consulting.fr/)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os

from odoo.modules import load_information_from_description_file


def main():
    module = os.path.basename(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))))
    d = load_information_from_description_file(module)
    with open('manifest', 'w') as out:
        manifest_content = (
                d['description']
                if 'description' in d
                else d['summary'] if 'summary' in d else '')
        out.write(manifest_content)


if __name__ == "__main__":
    main()
