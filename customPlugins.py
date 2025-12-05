import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaMPx as ommpx
import sys
import os


def create_cube():
    """Crée un cube dans la scène"""
    cmds.polyCube(name='mon_cube')
    print("Cube créé")


def select_only_meshes():
    """Sélectionne uniquement les mesh dans la sélection actuelle"""
    # Récupère la sélection actuelle ou tous les objets si rien n'est sélectionné
    selection = cmds.ls(sl=True, long=True) or cmds.ls(long=True)
    
    meshes = []
    for obj in selection:
        # Récupère les shapes de l'objet
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
        for shape in shapes:
            # Vérifie si c'est un mesh
            if cmds.nodeType(shape) == 'mesh':
                meshes.append(obj)
                break
    
    # Sélectionne les mesh trouvés
    if meshes:
        cmds.select(meshes, replace=True)
        print(f'{len(meshes)} mesh(es) selectionne(s)')
    else:
        cmds.select(clear=True)
        print('Aucun mesh trouve')
    
    return meshes


def delete_history():
    """Supprime l'historique de construction des mesh sélectionnés"""
    meshes = select_only_meshes()
    
    if meshes:
        for obj in meshes:
            cmds.delete(obj, ch=True)
        print(f"Historique supprimé pour {len(meshes)} mesh(es)")
    else:
        print("Aucun mesh sélectionné")


def freeze_transform():
    """Freeze les transformations des mesh sélectionnés"""
    meshes = select_only_meshes()
    
    if meshes:
        cmds.makeIdentity(meshes, apply=True, translate=True, rotate=True, scale=True, normal=False)
        print(f"Transformations freezées pour {len(meshes)} mesh(es)")
    else:
        print("Aucun mesh sélectionné")


def create_custom_shelf():
    """Crée un shelf personnalisé avec un bouton pour créer un cube"""
    
    shelf_name = "MesOutils"
    
    # Vérifie si le shelf existe déjà
    if cmds.shelfLayout(shelf_name, exists=True):
        # Supprime l'ancien shelf pour le recréer
        cmds.deleteUI(shelf_name, layout=True)
    
    # Crée le nouveau shelf
    main_shelf = cmds.shelfLayout(shelf_name, parent="ShelfLayout")
    
    # Ajoute un bouton pour créer un cube
    cmds.shelfButton(
        parent=main_shelf,
        label="Cube",
        command="from customPlugins import create_cube\ncreate_cube()",
        image="polyCube.png",
        annotation="Créer un cube",
        imageOverlayLabel="Cube",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour sélectionner uniquement les mesh
    cmds.shelfButton(
        parent=main_shelf,
        label="Mesh",
        command="from customPlugins import select_only_meshes\nselect_only_meshes()",
        image="polyMesh.png",
        annotation="Sélectionner uniquement les mesh dans la sélection",
        imageOverlayLabel="Mesh",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour supprimer l'historique
    cmds.shelfButton(
        parent=main_shelf,
        label="Del History",
        command="from customPlugins import delete_history\ndelete_history()",
        image="deleteHistory.png",
        annotation="Supprimer l'historique des mesh sélectionnés",
        imageOverlayLabel="DelH",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour freeze transform
    cmds.shelfButton(
        parent=main_shelf,
        label="Freeze",
        command="from customPlugins import freeze_transform\nfreeze_transform()",
        image="freezeTransform.png",
        annotation="Freeze les transformations des mesh sélectionnés",
        imageOverlayLabel="Frz",
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
    # Ajoute le chemin du dossier plug-ins au sys.path
    plugin_path = cmds.pluginInfo('customPlugins', query=True, path=True)
    plugin_dir = os.path.dirname(plugin_path)
    if plugin_dir not in sys.path:
        sys.path.append(plugin_dir)
    
    # Force le rechargement du module
    import importlib
    if 'customPlugins' in sys.modules:
        importlib.reload(sys.modules['customPlugins'])
    
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