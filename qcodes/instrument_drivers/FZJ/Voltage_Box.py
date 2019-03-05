from qcodes import ChannelList, Instrument, InstrumentChannel
from qcodes.utils.validators import Enum
import serial


class VoltageBoxChannel(InstrumentChannel):

    _channel_values = Enum('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
    _channel_ids = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8}

    def __init__(self, parent, name, channel):

        super().__init__(parent, name)

        # validate the channel value
        self._channel_values.validate(channel)
        self.channel = channel
        self.channel_id = self._channel_ids[channel]

        # voltage flag
        self.current_voltage = 0

        # add the various channel parameters
        if self.channel_id <= 4:
            self.add_parameter('current',
                               get_cmd=self.get_current,
                               get_parser=float,
                               label='current',
                               unit='nA')

        self.add_parameter('voltage',
                           get_cmd=self.get_voltage,
                           set_cmd=self.set_voltage,
                           label='voltage', # TODO: add limits
                           unit='V')

    # get methods
    def get_current(self):
        self._parent.comport.flushInput()
        self._parent.comport.flushOutput()
        self._parent.comport.write(str.encode('GVO_ADW:'+str(self.channel_id)+';\n'))
        answer = self._parent.comport.readline()
        current = str(answer)[2:-7]
        current = float(current.replace(",","."))
        return current

    def get_voltage(self):
        return self.current_voltage

    # set methods
    def set_voltage(self, voltage):
        self._parent.comport.flushInput()
        self._parent.comport.flushOutput()
        self._parent.comport.write(str.encode('GVO_DAK:'+str(self.channel_id)+';\n'))
        self._parent.comport.write(str.encode('GVO_DAW:'+str(voltage)+';\n'))
        self.current_voltage = voltage


class VoltageBox(Instrument):

    def __init__(self, name, com_port, **kwargs):

        super().__init__(name, **kwargs)

        # initialization
        self.comport = serial.Serial()
        self.comport.port = 'COM'+str(com_port)
        self.comport.timeout = 2
        self.comport.baudrate = 19200
        self.comport.open()

        # add the channels to the channel list
        channels = ChannelList(self, "VoltageBoxChannels", VoltageBoxChannel, snapshotable=False)
        for channel_id in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'):
            channel = VoltageBoxChannel(self, 'Chan{}'.format(channel_id), channel_id)
            channels.append(channel)
            self.add_submodule(channel_id, channel)
        channels.lock()
        self.add_submodule("channels", channels)

        # print connect message
        self.connect_message()
