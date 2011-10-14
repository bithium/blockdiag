# -*- coding: utf-8 -*-
#  Copyright 2011 Takeshi KOMIYA
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from blockdiag.noderenderer import NodeShape
from blockdiag.noderenderer import install_renderer
from blockdiag.utils.XY import XY


class LoopIn(NodeShape):
    def __init__(self, node, metrix=None):
        super(LoopIn, self).__init__(node, metrix)

        m = self.metrix.cell(self.node)
        xdiff = self.metrix.node_width / 4
        ydiff = self.metrix.node_height / 4

        textbox = (m.topleft.x, m.topleft.y + ydiff,
                   m.bottomright.x, m.bottomright.y)

    def render_shape(self, drawer, format, **kwargs):
        outline = kwargs.get('outline')
        fill = kwargs.get('fill')

        m = self.metrix.cell(self.node)
        xdiff = self.metrix.node_width / 4
        ydiff = self.metrix.node_height / 4

        shape = [XY(m.topleft.x + xdiff, m.topleft.y),
                 XY(m.topright.x - xdiff, m.topleft.y),
                 XY(m.topright.x, m.topright.y + ydiff),
                 XY(m.topright.x, m.bottomright.y),
                 XY(m.topleft.x, m.bottomleft.y),
                 XY(m.topleft.x, m.topleft.y + ydiff),
                 XY(m.topleft.x + xdiff, m.topleft.y)]

        # draw outline
        if kwargs.get('shadow'):
            shape = self.shift_shadow(shape)
            drawer.polygon(shape, fill=fill, outline=fill,
                           filter='transp-blur')
        elif self.node.background:
            drawer.polygon(shape, fill=self.node.color,
                             outline=self.node.color)
            drawer.loadImage(self.node.background, self.textbox)
            drawer.polygon(shape, fill="none", outline=outline,
                           style=self.node.style)
        else:
            drawer.polygon(shape, fill=self.node.color, outline=outline,
                           style=self.node.style)


def setup(self):
    install_renderer('flowchart.loopin', LoopIn)
