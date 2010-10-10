#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import sys
import uuid
from optparse import OptionParser
import DiagramDraw
import diagparser
from utils.XY import XY
import utils


class Screen:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.rankdir = None
        self.color = None

    def setAttributes(self, attrs):
        for attr in attrs:
            value = re.sub('^"?(.*?)"?$', '\\1', attr.value)

            if attr.name == 'rankdir':
                if value.upper() == 'LR':
                    self.rankdir = value.upper()
                else:
                    msg = "WARNING: unknown rankdir: %s\n" % value
                    sys.stderr.write(msg)
            elif attr.name == 'color':
                self.color = value
            else:
                msg = "Unknown node attribute: %s.%s" % (self.id, attr.name)
                raise AttributeError(msg)


class ScreenNode:
    @classmethod
    def getId(klass, node):
        try:
            node_id = node.id
        except AttributeError:
            node_id = node

        return node_id

    def __init__(self, id):
        self.id = id
        self.xy = XY(0, 0)
        self.group = None
        self.drawable = 1

        if id:
            self.label = re.sub('^"?(.*?)"?$', '\\1', id)
        else:
            self.label = ''
        self.color = (255, 255, 255)
        self.style = None
        self.numbered = None
        self.background = None
        self.width = 1
        self.height = 1

    def copyAttributes(self, other):
        if other.xy:
            self.xy = other.xy
        if other.label:
            self.label = other.label
        if other.color:
            self.color = other.color
        if other.style:
            self.style = other.style
        if other.numbered:
            self.numbered = other.numbered
        if other.background:
            self.background = other.background
        if other.width:
            self.width = other.width
        if other.height:
            self.height = other.height

    def setAttributes(self, attrs):
        for attr in attrs:
            value = re.sub('^"?(.*?)"?$', '\\1', attr.value)
            if attr.name == 'label':
                self.label = value
            elif attr.name == 'color':
                self.color = value
            elif attr.name == 'style':
                style = value.lower()
                if style in ('solid', 'dotted', 'dashed'):
                    self.style = style
                else:
                    msg = "WARNING: unknown edge style: %s\n" % style
                    sys.stderr.write(msg)
            elif attr.name == 'numbered':
                self.numbered = value
            elif attr.name == 'background':
                if os.path.isfile(value):
                    self.background = value
                else:
                    msg = "WARNING: background image not found: %s\n" % value
                    sys.stderr.write(msg)
            elif attr.name == 'width':
                self.width = int(value)
            elif attr.name == 'height':
                self.height = int(value)
            else:
                msg = "Unknown node attribute: %s.%s" % (self.id, attr.name)
                raise AttributeError(msg)


class ScreenEdge:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2
        self.circular = False
        self.crosspoints = []
        self.skipped = 0

        self.dir = 'forward'
        self.color = None
        self.style = None
        self.noweight = None

    def copyAttributes(self, other):
        if other.dir:
            self.dir = other.dir
        if other.color:
            self.color = other.color
        if other.style:
            self.style = other.style
        if other.noweight:
            self.noweight = other.noweight

    def setAttributes(self, attrs):
        for attr in attrs:
            value = re.sub('^"?(.*?)"?$', '\\1', attr.value)
            if attr.name == 'dir':
                dir = value.lower()
                if dir in ('back', 'both', 'none', 'forward'):
                    self.dir = dir
                else:
                    msg = "WARNING: unknown edge dir: %s\n" % dir
                    sys.stderr.write(msg)
            elif attr.name == 'color':
                self.color = value
            elif attr.name == 'style':
                style = value.lower()
                if style in ('solid', 'dotted', 'dashed'):
                    self.style = style
                else:
                    msg = "WARNING: unknown edge style: %s\n" % style
                    sys.stderr.write(msg)
            elif attr.name == 'noweight':
                if value.lower() == 'none':
                    self.noweight = None
                else:
                    self.noweight = 1
            else:
                raise AttributeError("Unknown edge attribute: %s" % attr.name)


class ScreenGroup(ScreenNode):
    def __init__(self, id):
        ScreenNode.__init__(self, id)
        self.label = ''
        self.nodes = []
        self.edges = []
        self.color = (243, 152, 0)
        self.width = 1
        self.height = 1
        self.drawable = 0

    def setSize(self, nodes):
        if len(nodes) > 0:
            self.width = max(x.xy.x for x in nodes) + 1
            self.height = max(x.xy.y for x in nodes) + 1


class ScreenNodeBuilder:
    @classmethod
    def build(klass, tree, group=False):
        return klass()._build(tree, group)

    def __init__(self):
        self.screen = Screen()
        self.uniqNodes = {}
        self.nodeOrder = []
        self.uniqLinks = {}
        self.heightRefs = []
        self.rows = 0

    def _build(self, tree, group=False):
        self.buildNodeList(tree)

        self.screen.nodes = self.uniqNodes.values()
        self.screen.edges = self.uniqLinks.values()

        if self.screen.rankdir == 'LR':
            for node in self.screen.nodes:
                i = node.width
                node.width = node.height
                node.height = i

                node.xy = XY(node.xy.y, node.xy.x)

        if not group:
            if self.screen.color:
                msg = "WARNING: diagram.color was ignored: %s\n" % \
                      self.screen.color
                sys.stderr.write(msg)

        return self.screen

    def getScreenNode(self, id):
        if id in self.uniqNodes:
            node = self.uniqNodes[id]
        else:
            node = ScreenNode(id)
            self.uniqNodes[id] = node
            self.nodeOrder.append(node)

        return node

    def getScreenGroup(self, id):
        if id is None:
            # generate new id
            id = 'ScreenGroup %s' % uuid.uuid1()
        else:
            id = 'ScreenGroup %s' % id

        if id in self.uniqNodes:
            group = self.uniqNodes[id]
        else:
            group = ScreenGroup(id)
            self.uniqNodes[id] = group
            self.nodeOrder.append(group)

        return group

    def getScreenEdge(self, id1, id2):
        link = (self.getScreenNode(id1), self.getScreenNode(id2))

        if link in self.uniqLinks:
            edge = self.uniqLinks[link]
        else:
            edge = ScreenEdge(link[0], link[1])
            self.uniqLinks[link] = edge

        return edge

    def getChildren(self, node):
        node_id = ScreenNode.getId(node)

        uniq = {}
        for edge in self.uniqLinks.values():
            if edge.noweight or edge.circular:
                continue

            if node_id == None:
                uniq[edge.node1] = 1
            elif edge.node1.id == node_id:
                uniq[edge.node2] = 1
            elif edge.node1.group and edge.node1.group.id == node_id:
                uniq[edge.node2] = 1

        children = []
        for node in uniq.keys():
            if node.group:
                children.append(node.group)
            else:
                children.append(node)

        order = self.nodeOrder
        children.sort(lambda x, y: cmp(order.index(x), order.index(y)))

        return children

    def isCircularRef(self, node1, node2):
        node1_id = ScreenNode.getId(node1)

        referenced = False
        children = [node2]
        uniqNodes = {}
        for child in children:
            if node1_id == child.id:
                referenced = True
                break

            for node in self.getChildren(child):
                if not node in uniqNodes:
                    children.append(node)
                    uniqNodes[node] = 1

        return referenced

    def setNodeWidth(self, depth=0):
        for node in self.nodeOrder:
            if node.xy.x != depth or node.group is not None:
                continue

            o1 = self.nodeOrder.index(node)
            for child in self.getChildren(node):
                o2 = self.nodeOrder.index(child)
                if o1 > o2 and self.isCircularRef(node, child):
                    edge = self.getScreenEdge(node.id, child.id)
                    edge.circular = True
                elif node == child:
                    pass
                elif child.group:
                    pass
                else:
                    child.xy = XY(node.xy.x + node.width, 0)

        depther_node = [x for x in self.nodeOrder if x.xy.x > depth]
        if len(depther_node) > 0:
            self.setNodeWidth(depth + 1)

    def setNodeHeight(self, node, baseHeight):
        node.xy = XY(node.xy.x, baseHeight)
        self.heightRefs.append(node.id)

        height = 0
        for child in self.getChildren(node):
            if child.id in self.heightRefs:
                pass
            elif node.xy.x < child.xy.y:
                pass
            else:
                height += self.setNodeHeight(child, baseHeight + height)

        if height < node.height:
            height = node.height

        return height

    def buildNodeGroup(self, group, tree):
        nodes = [x.id for x in tree.stmts if isinstance(x, diagparser.Node)]
        for edge in self.uniqLinks.values():
            node1_id = edge.node1.id
            node2_id = edge.node2.id

            if node1_id in nodes and node2_id in nodes:
                edge = diagparser.Edge([node1_id, node2_id], [])
                tree.stmts.append(edge)

        screen = ScreenNodeBuilder.build(tree, group=True)
        if len(screen.nodes) == 0:
            del self.uniqNodes[group.id]
            self.nodeOrder.remove(group)
            return

        if screen.color:
            group.color = screen.color

        group.setSize(screen.nodes)

        for node in screen.nodes:
            n = self.getScreenNode(node.id)
            if n.group:
                msg = "ScreenNode could not belong to two groups"
                raise RuntimeError(msg)
            n.copyAttributes(node)
            n.group = group

            group.nodes.append(n)

        for edge in screen.edges:
            e = self.getScreenEdge(edge.node1.id, edge.node2.id)
            e.copyAttributes(edge)
            e.group = group

            group.edges.append(e)

    def buildNodeList(self, tree):
        nodeGroups = {}
        for stmt in tree.stmts:
            if isinstance(stmt, diagparser.Node):
                node = self.getScreenNode(stmt.id)
                node.setAttributes(stmt.attrs)
            elif isinstance(stmt, diagparser.Edge):
                while len(stmt.nodes) >= 2:
                    edge = self.getScreenEdge(stmt.nodes.pop(0), stmt.nodes[0])
                    edge.setAttributes(stmt.attrs)
            elif isinstance(stmt, diagparser.SubGraph):
                group = self.getScreenGroup(stmt.id)
                nodeGroups[group] = stmt
            elif isinstance(stmt, diagparser.DefAttrs):
                self.screen.setAttributes(stmt.attrs)
            else:
                raise AttributeError("Unknown sentense: " + str(type(stmt)))

        for group in nodeGroups:
            self.buildNodeGroup(group, nodeGroups[group])

        self.setNodeWidth()

        height = 0
        toplevel_nodes = [x for x in self.nodeOrder if x.xy.x == 0]
        for node in toplevel_nodes:
            if not node.group:
                height += self.setNodeHeight(node, height)

        for node in self.nodeOrder:
            if isinstance(node, ScreenGroup):
                for child in node.nodes:
                    child.xy = XY(node.xy.x + child.xy.x,
                                  node.xy.y + child.xy.y)


def main():
    usage = "usage: %prog [options] infile"
    p = OptionParser(usage=usage)
    p.add_option('-a', '--antialias', action='store_true',
                 help='Pass diagram image to anti-alias filter')
    p.add_option('-o', dest='filename',
                 help='write diagram to FILE', metavar='FILE')
    p.add_option('-f', '--font', dest='font',
                 help='use FONT to draw diagram', metavar='FONT')
    p.add_option('-P', '--pdb', dest='pdb', action='store_true', default=False,
                 help='Drop into debugger on exception')
    p.add_option('-T', dest='type', default='PNG',
                 help='Output diagram as TYPE format')
    (options, args) = p.parse_args()

    if len(args) == 0:
        p.print_help()
        exit(0)

    format = options.type.upper()
    if not format in ('SVG', 'PNG'):
        msg = "ERROR: unknown format: %s\n" % options.type
        sys.stderr.write(msg)
        exit(0)

    fonts = [options.font,
             'c:/windows/fonts/VL-Gothic-Regular.ttf',
             'c:/windows/fonts/msmincho.ttf',
             '/usr/share/fonts/truetype/ipafont/ipagp.ttf',
             '/System/Library/Fonts/AppleGothic.ttf']

    fontpath = None
    for path in fonts:
        if path and os.path.isfile(path):
            fontpath = path
            break

    infile = args[0]
    if options.filename:
        outfile = options.filename
    else:
        outfile = re.sub('\..*', '', infile) + '.' + options.type.lower()

    if options.pdb:
        sys.excepthook = utils.postmortem

    tree = diagparser.parse_file(infile)
    screen = ScreenNodeBuilder.build(tree)

    draw = DiagramDraw.DiagramDraw(format, screen, font=fontpath,
                                   antialias=options.antialias)
    draw.draw()
    draw.save(outfile)


if __name__ == '__main__':
    main()
