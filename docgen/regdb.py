
import yaml

class RegisterGroup:
    """Class which contains information about one group of registers"""

    def __init__(self):
        self.registers = []
    name = ''
    offset = 0
    size = 0
    brief = ''
    desc = ''

class Register:
    """Class which contains information about a single register"""
    def __init__(self):
        self.bits = []
    name = ''
    offset = 0
    brief = ''
    desc = ''
    access = '?'
    array = False
    count = 1
    stride = 0

class Bitfield:
    low = 0
    high = 0
    access = '?'
    name = ''
    brief = ''
    desc = ''

class ArrayInfo:
    count = 1
    stride = 0

class RegisterDatabase:
    """Class which parses a register database file"""

    groups = []

    def __init__(self, filename):
        # Open the YAML file
        mmiofile = file(filename, 'r')
        mmio = yaml.load(mmiofile)
        # Read the data
        self._parseGroup(mmio, '', 0, None, None)
        # Sort the groups by offset
        self.groups = sorted(self.groups,
                             key=lambda group: group.offset)

    def _parseGroup(self, dblist, prefix, offset, parent, array_info):
        # Create the group
        # TODO: Anonymous groups?
        if prefix != '' and 'name' in dblist:
            name = prefix + '_' + dblist['name']
        elif prefix != '':
            name = prefix
        elif 'name' in dblist:
            name = dblist['name']
        else:
            name = ''
        group = RegisterGroup()
        group.name = name
        group.offset = offset
        if 'offset' in dblist:
            group.offset += dblist['offset']
        if 'size' in dblist:
            group.size = dblist['size']
        if 'brief' in dblist:
            group.brief = dblist['brief']
        if 'desc' in dblist:
            group.desc = dblist['desc']
        # Create all registers and subgroups in the group
        if 'bare' in dblist and dblist['bare']:
            prefix = ''
        else:
            prefix = name

        if 'blocks' in dblist:
            for choffset, child in dblist['blocks'].iteritems():
                self._parseGroup(child, prefix, group.offset + choffset, parent,
                                 array_info)
        if 'registers' in dblist:
            for choffset, child in dblist['registers'].iteritems():
                self._parseRegister(child, group, prefix,
                                    group.offset + choffset, parent,
                                    array_info)
        if 'arrays' in dblist:
            for choffset, child in dblist['arrays'].iteritems():
                self._parseArray(child, group, prefix,
                                 group.offset + choffset, parent,
                                 array_info)
        # Sort the registers by offset
        group.registers = sorted(group.registers,
                                 key=lambda register: register.offset)
        # Skip empty groups
        if parent is None and (len(group.registers) != 0
                               or group.brief != ''
                               or group.desc != ''):
            self.groups.append(group)

    def _parseArray(self, dblist, group, prefix, offset, parent, array_info):
        if array_info != None:
            print("Warning: Nested arrays not supported yet!")
            return
        array = ArrayInfo()
        array.count = dblist['length']
        array.stride = dblist['stride']
        if 'name' in dblist:
            prefix = prefix + '_' + dblist['name']
        if 'block' in dblist:
            self._parseGroup(dblist['block'], prefix, offset, group, array)
        if 'register' in dblist:
            # TODO
            pass
        pass

    def _parseRegister(self, dblist, group, prefix, offset, parent, array_info):
        # Create the register
        localoffset = 0
        if 'offset' in dblist:
            localoffset = dblist['offset']
        if 'name' in dblist:
            localname = dblist['name']
        else:
            localname = "UNK_" + hex(localoffset)
        register = Register()
        register.offset = offset + localoffset
        if prefix != '':
            register.name = prefix + '_' + localname
        else:
            register.name = localname
        if 'brief' in dblist:
            register.brief = dblist['brief']
        if 'desc' in dblist:
            register.desc = dblist['desc']
        if array_info != None:
            register.array = True
            register.count = array_info.count
            register.stride = array_info.stride
        if parent != None:
            parent.registers.append(register)
        else:
            group.registers.append(register)
        # Parse the bitfields
        if 'bits' in dblist:
            self._parseBitfields(dblist['bits'], register)
        # If no bitfields are present, create one large field
        if len(register.bits) == 0:
            bitfield = Bitfield()
            bitfield.low = 0
            bitfield.high = 31
            register.bits.append(bitfield)
        register.bits = sorted(register.bits,
                               key=lambda bitfield: bitfield.low)

    def _parseBitfields(self, dblist, register):
        for bitrange, entry in dblist.iteritems():
            bitfield = Bitfield()
            if type(bitrange) is int:
                bitfield.high = bitfield.low = bitrange
            else:
                words = bitrange.split('-')
                if not len(words) == 2:
                    print("Warning: Invalid bit range specification.")
                    return
                bitfield.high = max(int(words[0]), int(words[1]))
                bitfield.low = min(int(words[0]), int(words[1]))
            if 'name' in entry:
                bitfield.name = entry['name']
            else:
                bitfield.name = 'UNK_' + str(bitfield.low)
            if 'brief' in entry:
                bitfield.brief = entry['brief']
            if 'desc' in entry:
                bitfield.desc = entry['desc']
            register.bits.append(bitfield)
            pass