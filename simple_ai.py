# SPDX-License-Identifier: BSD-3-Clause

import numpy as np

from supremacy import helpers

# This is your team name
CREATOR = "John"

TYPES = {}
JET_Y_CORDS = {}
JET_X_CORDS = {}
BASE_TARGETS = {}


def tank_ai(tank, info, game_map):
    """
    Function to control tanks.
    """
    if not tank.stopped:
        if tank.stuck:
            tank.set_heading(np.random.random() * 360.0)
        elif "target" in info:
            tank.goto(*info["target"])


def ship_ai(ship, info, game_map):
    """
    Function to control ships.
    """
    radius = 80
    if ship.uid not in TYPES:
         TYPES[ship.uid] = "explorer"
         print(f"setting SHIP {ship.uid} to explorer")
    if TYPES[ship.uid] == "explorer":
        if not ship.stopped:
            if ship.stuck:
                # go over bases
                alone = True
                for b in info["bases"]:
                    if ship.get_distance(b.x, b.y) < radius:
                        alone = False
                        break
                if alone:
                    ship.convert_to_base()
                else:
                    ship.set_heading(np.random.random() * 360.0)
    else:
        #list all bases:
        print("UNKNOWN TYPE of the SHIP")
        pass
            

def jet_ai(jet, info, game_map):
    """
    Function to control jets.
    """
    if jet.uid not in TYPES:
        # max explorers
        maxexp = game_map.shape[0] / 20
        if len(JET_Y_CORDS) < maxexp:
            ttype = "explorer1"
        else:
            ttype = "attacker"            
        TYPES[jet.uid] = ttype
        print(f"setting JET {jet.uid} to {ttype}")
    if TYPES[jet.uid] == "explorer1":
        # get empty row
        ypos = -1e6
        ## arrived?
        if jet.uid not in JET_Y_CORDS:
            if len(JET_Y_CORDS) == 0:
                ypos = jet.owner.y
            else:
                for v in JET_Y_CORDS.values():
                    ypos = max(ypos, v)
                ypos = ypos + 20
            JET_Y_CORDS[jet.uid] = ypos
            jet.goto(jet.owner.x, ypos)
        else:
            if abs(JET_Y_CORDS[jet.uid] % game_map.shape[0]-jet.y) < 4:
                print(f"Explorer1 arrived, next level!")
                TYPES[jet.uid] = "explorer2"
    if TYPES[jet.uid] == "explorer2":
        if jet.uid not in JET_X_CORDS:
            JET_X_CORDS[jet.uid] = (jet.owner.x + game_map.shape[1] / 2) % game_map.shape[1]
            #left right?
            if len(JET_X_CORDS) % 2 == 0:
                jet.goto(jet.x + 100, JET_Y_CORDS[jet.uid])
            else:
                jet.goto(jet.x - 100, JET_Y_CORDS[jet.uid])
        elif abs(JET_X_CORDS[jet.uid]-jet.x) < 4:
            print(f"Explorer2 arrived, next level!")
            TYPES[jet.uid] = "attacker"
    if TYPES[jet.uid] == "attacker":
        shortest = 1e9
        target = [0,0]
        for b in info["ebases"]:
            if jet.get_distance(b.x, b.y) < shortest:
                target = [b.x,b.y]
                shortest = jet.get_distance(b.x, b.y)
        jet.goto(*target)
        


class PlayerAi:
    """
    This is the AI bot that will be instantiated for the competition.
    """

    blevels = {}

    def __init__(self):
        self.team = CREATOR  # Mandatory attribute


    def build(self, base, kind = "mine"):
        if base.crystal < base.cost(kind):
            return None
        else:
            kwargs = {}
            if kind != "mine":
                kwargs["heading"] = 360 * np.random.random()
            build = getattr(base, f"build_{kind}")(**kwargs)
            return True




    def run(self, t: float, dt: float, info: dict, game_map: np.ndarray):
        """
        This is the main function that will be called by the game engine.
        """

        # Get information about my team
        myinfo = info[self.team]
        myinfo["ebases"] = []

        # Iterate through all my bases and process build queue
        for b in myinfo["bases"]:
            if b.uid not in self.blevels:
                lvl = 0
            else:
                lvl = self.blevels[b.uid]
            if lvl < 2:
                bb = self.build(b, "mine")
            elif lvl == 4:
                bb = self.build(b, "mine")
            elif lvl == 10:
                bb = self.build(b, "mine")
            elif lvl < 12:
                bb = self.build(b, "ship")
            else:
                if lvl % 3 == 0:
                    bb = self.build(b, "ship")
                else:
                    bb = self.build(b, "jet")                    
            if bb:
                print(f"mine done at {lvl=}")
                self.blevels[b.uid] = lvl+1

        # Try to find an enemy target
        # If there are multiple teams in the info, find the first team that is not mine
        if len(info) > 1:
            for name in info:
                if name != self.team:
                    # Target only bases
                    if "bases" in info[name]:
                        # Simply target the first base
                        for b in info[name]["bases"]:
                            myinfo["ebases"].append(b)
                        t = info[name]["bases"][0]
                        print(f"BASE of {name} targeted!")
                        myinfo["target"] = [t.x, t.y]
                        break

        # Control all my vehicles
        helpers.control_vehicles(
            info=myinfo, game_map=game_map, tank=tank_ai, ship=ship_ai, jet=jet_ai
        )
