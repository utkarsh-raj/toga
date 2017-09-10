from rubicon.objc import *
from ..libs import *
from ..utils import process_callback
from .base import WidgetMixin


class TogaNodeData(NSObject):
    @objc_method
    def copyWithZone_(self):
        copy = TogaNodeData.alloc().init()
        copy.node = self.node
        return copy


class TogaIconCell(NSTextFieldCell):
    @objc_method
    def drawWithFrame_inView_(self, cellFrame: NSRect, view) -> None:
        # The data to display
        print("DRAW", self.objectValue)
        label = self.objectValue.node.data[0]
        icon = self.objectValue.node.icon

        if icon:
            offset = 18

            NSGraphicsContext.currentContext.saveGraphicsState()
            yOffset = cellFrame.origin.y
            if view.isFlipped:
                xform = NSAffineTransform.transform()
                xform.translateXBy(0.0, yBy=cellFrame.size.height)
                xform.scaleXBy(1.0, yBy=-1.0)
                xform.concat()
                yOffset = 0 - cellFrame.origin.y;

            interpolation = NSGraphicsContext.currentContext.imageInterpolation
            NSGraphicsContext.currentContext.imageInterpolation = NSImageInterpolationHigh

            icon.drawInRect(
                NSRect(NSPoint(cellFrame.origin.x, yOffset), NSSize(16.0, 16.0)),
                fromRect=NSRect(NSPoint(0, 0), NSSize(icon.size.width, icon.size.height)),
                operation=NSCompositingOperationSourceOver,
                fraction=1.0
            )

            NSGraphicsContext.currentContext.imageInterpolation = interpolation
            NSGraphicsContext.currentContext.restoreGraphicsState()
        else:
            # No icon; just the text label
            offset = 0

        if label:
            # Find the right color for the text
            if self.isHighlighted():
                primaryColor = NSColor.alternateSelectedControlTextColor
            else:
                if False:
                    primaryColor = NSColor.disabledControlTextColor
                else:
                    primaryColor = NSColor.textColor

            textAttributes = NSMutableDictionary.alloc().init()
            textAttributes[NSForegroundColorAttributeName] = primaryColor
            textAttributes[NSFontAttributeName] = NSFont.systemFontOfSize(13)

            at(label).drawAtPoint(
                NSPoint(cellFrame.origin.x + offset, cellFrame.origin.y),
                withAttributes=textAttributes
            )


class TogaTree(NSOutlineView):
    # OutlineViewDataSource methods
    @objc_method
    def outlineView_child_ofItem_(self, tree, child: int, item):
        print("GET CHILD", child, "of item", item)
        if item is None:
            node = self.interface.data.root(child)
        else:
            parent = self.interface.data.node(item)
            node = parent.children[child]

        print("NODE IS", node)
        if node._impl is None:
            if node.icon:
                icon = NSImage.alloc().initWithContentsOfFile_(node.icon)
            else:
                icon = None

            # node._impl = TogaNodeData.alloc().initWithLabel(list(node.data), icon=icon)
            node._impl = TogaNodeData.alloc().init()
            node._impl.node = node

            print("CREATED IMPL", node._impl)

        return node._impl

    @objc_method
    def outlineView_isItemExpandable_(self, tree, item) -> bool:
        return self.interface.data.node(item).children is not None

    @objc_method
    def outlineView_numberOfChildrenOfItem_(self, tree, item) -> int:
        if item is None:
            if self.interface.data:
                return len(self.interface.data.roots())
            else:
                return 0
        else:
            return len(self.interface.data.node(item).children)

    @objc_method
    def outlineView_objectValueForTableColumn_byItem_(self, tree, column, item):
        return self.interface.data.node(item)._impl
        # if column.identifier == '0':

        # else:
        #     return self.interface.data.node(item).label(int(column.identifier))

    # OutlineViewDelegate methods
    @objc_method
    def outlineViewSelectionDidChange_(self, notification) -> None:
        print("tree selection changed")


class Tree(Widget):
    def create(self):
        self.tree = None
        self.columns = None

        # Create a tree view, and put it in a scroll view.
        # The scroll view is the _impl, because it's the outer container.
        self.native = NSScrollView.alloc().init()
        self.native.hasVerticalScroller = True
        self.native.hasHorizontalScroller = False
        self.native.autohidesScrollers = False
        self.native.borderType = NSBezelBorder

        # Disable all autolayout functionality on the outer widget
        self.native.translatesAutoresizingMaskIntoConstraints = False
        self.native.autoresizesSubviews = True

        self.tree = TogaTree.alloc().init()
        self.tree.interface = self.interface
        self.tree._impl = self
        self.tree.columnAutoresizingStyle = NSTableViewUniformColumnAutoresizingStyle

        # Use autolayout for the inner widget.
        self.tree.translatesAutoresizingMaskIntoConstraints = True

        # Create columns for the tree
        self.columns = [
            NSTableColumn.alloc().initWithIdentifier_('%d' % i)
            for i, heading in enumerate(self.interface.headings)
        ]

        for heading, column in zip(self.interface.headings, self.columns):
            self.tree.addTableColumn(column)

            column.dataCell = TogaIconCell.alloc().init()
            cell = column.dataCell
            cell.editable = False
            cell.selectable = False

            column.headerCell.stringValue = heading

        # Put the tree arrows in the first column.
        self.tree.outlineTableColumn = self.columns[0]

        self.tree.delegate = self.tree
        self.tree.dataSource = self.tree

        # Embed the tree view in the scroll view
        self.native.documentView = self.tree

        # Add the layout constraints
        self.add_constraints()

    def refresh_node(self, node):
        if node._expanded:
            self.tree.expandItem(node.native)
        else:
            self.tree.collapseItem(node.native)

        # Reconstruct the native object.
        if node.icon:
            icon = NSImage.alloc().initWithContentsOfFile_(node.icon)
        else:
            icon = None

        node.native = TogaNodeData.alloc().init()
        node.native.node = node

    def refresh(self):
        self.tree.reloadData()
