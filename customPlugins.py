import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaMPx as ommpx


def create_custom_shelf():
    """Crée un shelf personnalisé avec un bouton pour créer un cube"""
    
    shelf_name = "Thomaaas"
    
    # Vérifie si le shelf existe déjà
    if cmds.shelfLayout(shelf_name, exists=True):
        # Supprime l'ancien shelf pour le recréer
        cmds.deleteUI(shelf_name, layout=True)
    
    # Crée le nouveau shelf
    main_shelf = cmds.shelfLayout(shelf_name, parent="ShelfLayout")
    
    # Ajoute un bouton pour créer un cube
    cmds.shelfButton(
        parent=main_shelf,
        command="import maya.cmds as cmds\ncmds.polyCube(name='mon_cube')",
        image="polyCube.png",  # Icône Maya par défaut pour les cubes
        annotation="Créer un cube",
        imageOverlayLabel="Cube",
        style="iconOnly"
    )
    
    print(f"Shelf '{shelf_name}' créé avec succès!")


# Commande Maya pour créer le shelf
class CreateCustomShelfCommand(ommpx.MPxCommand):
    kPluginCmdName = "createCustomShelf"
    
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    @staticmethod
    def cmdCreator():
        return ommpx.asMPxPtr(CreateCustomShelfCommand())
    
    def doIt(self, args):
        create_custom_shelf()


def initializePlugin(mobject):
    """Initialise le plugin lors du chargement"""
    pluginFn = ommpx.MFnPlugin(mobject, "Votre Nom", "1.0", "Any")
    
    try:
        pluginFn.registerCommand(
            CreateCustomShelfCommand.kPluginCmdName,
            CreateCustomShelfCommand.cmdCreator
        )
        print("Plugin Custom Shelf chargé avec succès!")
        
        # Crée automatiquement le shelf au chargement du plugin
        create_custom_shelf()
        
    except:
        om.MGlobal.displayError("Erreur lors du chargement du plugin")


def uninitializePlugin(mobject):
    """Nettoie le plugin lors du déchargement"""
    pluginFn = ommpx.MFnPlugin(mobject)
    
    try:
        pluginFn.deregisterCommand(CreateCustomShelfCommand.kPluginCmdName)
        
        # Optionnel : supprime le shelf lors du déchargement
        # shelf_name = "MesOutils"
        # if cmds.shelfLayout(shelf_name, exists=True):
        #     cmds.deleteUI(shelf_name, layout=True)
        
        print("Plugin Custom Shelf déchargé")
    except:
        om.MGlobal.displayError("Erreur lors du déchargement du plugin")


        