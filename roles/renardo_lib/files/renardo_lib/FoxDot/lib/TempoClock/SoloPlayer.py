
class SoloPlayer:
    """ SoloPlayer objects """
    def __init__(self):
        self.data = []

    def __repr__(self):
        if len(self.data) == 0:
            return "None"
        if len(self.data) == 1:
            return repr(self.data[0])
        else:
            return repr(self.data)

    def add(self, player):
        if player not in self.data:
            self.data.append(player)

    def set(self, player):
        self.data = [player]

    def reset(self):
        self.data = []

    def active(self):
        """ Returns true if self.data is not empty """
        return len(self.data) > 0

    def __eq__(self, other):
        """ Returns true if other is in self.data or if self.data is empty """
        return (other in self.data) if self.data else True

    def __ne__(self, other):
        return (other not in self.data) if self.data else True
