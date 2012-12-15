
import os
import configshell


class Logs(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Logs, self).__init__('logs', parent)

    def ui_command_tail(self):
        '''
        tail - Tails syslog
        '''
        os.system("tail -qF /var/log/debug /var/log/syslog | ccze -A")
