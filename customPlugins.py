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


def assign_unique_materials():
    """Assigne un matériau aiStandardSurface unique à chaque mesh sélectionné"""
    # Vérifie si il y a une sélection
    selection = cmds.ls(sl=True)
    if not selection:
        cmds.error("Aucune sélection ! Veuillez sélectionner au moins un objet.")
        return
    
    # Filtre uniquement les mesh
    meshes = select_only_meshes()
    
    if not meshes:
        cmds.error("Aucun mesh trouvé dans la sélection !")
        return
    
    # Crée un matériau unique pour chaque mesh
    for mesh in meshes:
        # Récupère le nom court de l'objet
        short_name = mesh.split('|')[-1]
        
        # Crée un shader aiStandardSurface
        shader = cmds.shadingNode('aiStandardSurface', asShader=True, name=f"{short_name}_mat")
        
        # Crée un shading group
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f"{short_name}_SG")
        
        # Connecte le shader au shading group
        cmds.connectAttr(f"{shader}.outColor", f"{shading_group}.surfaceShader", force=True)
        
        # Assigne le matériau au mesh
        cmds.sets(mesh, edit=True, forceElement=shading_group)
        
        print(f"Matériau '{shader}' assigné à '{short_name}'")
    
    print(f"Matériaux assignés à {len(meshes)} mesh(es)")


def remove_pasted_prefix():
    """Enlève le préfixe 'pasted__' de tous les objets dans la scène"""
    # Sélectionne tout dans la scène
    all_objects = cmds.ls()
    
    renamed_count = 0
    
    for obj in all_objects:
        # Vérifie si le nom contient "pasted__"
        if "pasted__" in obj:
            # Enlève le préfixe "pasted__"
            new_name = obj.replace("pasted__", "")
            
            try:
                cmds.rename(obj, new_name)
                renamed_count += 1
                print(f"Renommé: '{obj}' -> '{new_name}'")
            except:
                print(f"Impossible de renommer: '{obj}'")
    
    if renamed_count > 0:
        print(f"{renamed_count} objet(s) renommé(s)")
    else:
        print("Aucun objet avec 'pasted__' trouvé")


def delete_empty_groups():
    """Supprime tous les groupes vides dans la scène"""
    deleted_count = 0
    
    # Boucle jusqu'à ce qu'il n'y ait plus de groupes vides
    # (car supprimer un groupe peut rendre son parent vide)
    while True:
        # Récupère tous les transforms
        all_transforms = cmds.ls(type='transform')
        empty_groups = []
        
        for obj in all_transforms:
            # Vérifie si l'objet n'a pas d'enfants
            children = cmds.listRelatives(obj, children=True, fullPath=True)
            
            if not children:
                empty_groups.append(obj)
        
        # Si aucun groupe vide trouvé, on arrête
        if not empty_groups:
            break
        
        # Supprime les groupes vides
        for grp in empty_groups:
            try:
                cmds.delete(grp)
                deleted_count += 1
                print(f"Groupe vide supprimé: '{grp}'")
            except:
                print(f"Impossible de supprimer: '{grp}'")
    
    if deleted_count > 0:
        print(f"{deleted_count} groupe(s) vide(s) supprimé(s)")
    else:
        print("Aucun groupe vide trouvé")


def setup_arnold_render():
    """Configure les paramètres de rendu Arnold pour le compositing"""
    
    # Charge le plugin Arnold si nécessaire
    if not cmds.pluginInfo("mtoa", query=True, loaded=True):
        try:
            cmds.loadPlugin("mtoa")
        except:
            print("Impossible de charger le plugin Arnold (mtoa)")
            return
    
    # Définir Arnold comme moteur de rendu
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
    
    # Résolution 1920x1080
    cmds.setAttr("defaultResolution.width", 1920)
    cmds.setAttr("defaultResolution.height", 1080)
    
    # Format EXR (40 = EXR dans Maya)
    cmds.setAttr("defaultRenderGlobals.imageFormat", 40)
    
    # Merge AOVs activé
    cmds.setAttr("defaultArnoldDriver.mergeAOVs", 1)
    
    # Frame/Animation extension : name.###.ext
    cmds.setAttr("defaultRenderGlobals.animation", 1)
    cmds.setAttr("defaultRenderGlobals.putFrameBeforeExt", 1)
    cmds.setAttr("defaultRenderGlobals.extensionPadding", 3)
    
    # Range 0-120
    cmds.setAttr("defaultRenderGlobals.startFrame", 0)
    cmds.setAttr("defaultRenderGlobals.endFrame", 120)
    
    # Active le rendu GPU sur Windows
    import platform
    if platform.system() == "Windows":
        try:
            cmds.setAttr("defaultArnoldRenderOptions.renderDevice", 1)  # 0=CPU, 1=GPU
            print("Rendu GPU activé (Windows)")
        except:
            print("Impossible d'activer le rendu GPU")
    else:
        print(f"Système détecté: {platform.system()} - GPU non activé (Windows uniquement)")
    
    # Import du module Arnold
    try:
        import mtoa.aovs as aovs
    except ImportError:
        print("Impossible d'importer le module mtoa.aovs")
        return
    
    # Active les AOVs principaux pour le compositing
    aovs_to_create = [
        "RGBA",
        "diffuse",
        "specular",
        "transmission",
        "sss",
        "emission",
        "volume",
        "N",
        "Z",
        "crypto_asset",
        "crypto_object",
        "crypto_material"
    ]
    
    # Crée les AOVs avec le module mtoa
    for aov_name in aovs_to_create:
        try:
            # Vérifie si l'AOV existe déjà
            existing_aovs = aovs.AOVInterface().getAOVNodes()
            aov_exists = False
            
            for existing_aov in existing_aovs:
                if cmds.getAttr(f"{existing_aov}.name") == aov_name:
                    aov_exists = True
                    print(f"AOV déjà existant (ignoré): {aov_name}")
                    break
            
            # Ajoute l'AOV seulement s'il n'existe pas
            if not aov_exists:
                aovs.AOVInterface().addAOV(aov_name)
                print(f"AOV ajouté: {aov_name}")
        except Exception as e:
            print(f"Erreur pour {aov_name}: {str(e)}")
    
    print("=" * 50)
    print("Preset Arnold configuré avec succès!")
    print("Résolution: 1920x1080")
    print("Format: EXR (Merge AOVs activé)")
    print("Animation: Frame 0-120 (name.###.ext)")
    print("AOVs activés pour le compositing")
    print("=" * 50)


def setup_lookdev_scene():
    """Configure une scène lookdev avec HDRI et caméra pour la sélection"""
    
    # Vérifie la sélection
    selection = cmds.ls(sl=True)
    if not selection:
        cmds.error("Aucune sélection ! Veuillez sélectionner au moins un objet.")
        return
    
    # Appelle setup_arnold_render
    setup_arnold_render()
    
    # Calcule le bounding box de la sélection
    bbox = cmds.exactWorldBoundingBox(selection)
    
    # Extraction des dimensions
    min_x, min_y, min_z = bbox[0], bbox[1], bbox[2]
    max_x, max_y, max_z = bbox[3], bbox[4], bbox[5]
    
    # Calcul du centre
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    
    # Calcul de la taille
    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    
    print(f"Centre de la sélection: X={center_x}, Y={center_y}, Z={center_z}")
    print(f"Taille de la sélection: X={size_x}, Y={size_y}, Z={size_z}")
    
    # Masque tout sauf la sélection
    all_objects = cmds.ls(dag=True, visible=True, transforms=True)
    for obj in all_objects:
        if obj not in selection and cmds.objExists(obj):
            try:
                cmds.setAttr(f"{obj}.visibility", 0)
            except:
                pass
    
    print(f"{len(all_objects) - len(selection)} objet(s) masqué(s)")
    
    # Crée le skydome HDRI
    skydome = cmds.shadingNode('aiSkyDomeLight', asLight=True, name='HDRI_SkyDome')
    
    # Position du skydome au centre de la sélection
    hdri_x = center_x
    hdri_y = center_y
    hdri_z = center_z
    
    cmds.setAttr(f"{skydome}.translateX", hdri_x)
    cmds.setAttr(f"{skydome}.translateY", hdri_y)
    cmds.setAttr(f"{skydome}.translateZ", hdri_z)
    
    print(f"HDRI créé à la position: X={hdri_x}, Y={hdri_y}, Z={hdri_z}")
    
    # Crée la caméra
    camera = cmds.camera(name='LookDev_Camera')
    camera_transform = camera[0]
    
    # Crée l'aim (locator)
    aim = cmds.spaceLocator(name='Camera_Aim')[0]
    
    # Position de la caméra
    cam_x = center_x
    cam_y = center_y * 1.2  # 20% de plus du centre en Y
    cam_z = center_z + (size_z * 4)  # 4x la taille en Z
    
    cmds.setAttr(f"{camera_transform}.translateX", cam_x)
    cmds.setAttr(f"{camera_transform}.translateY", cam_y)
    cmds.setAttr(f"{camera_transform}.translateZ", cam_z)
    
    # Position de l'aim (au centre comme HDRI)
    aim_x = center_x
    aim_y = center_y
    aim_z = center_z
    
    cmds.setAttr(f"{aim}.translateX", aim_x)
    cmds.setAttr(f"{aim}.translateY", aim_y)
    cmds.setAttr(f"{aim}.translateZ", aim_z)
    
    # Contrainte aim sur la caméra
    cmds.aimConstraint(aim, camera_transform, aimVector=[0, 0, -1], upVector=[0, 1, 0])
    
    # Animation : double 360° sur 120 frames autour de l'aim
    # Crée un groupe pour faire tourner la caméra autour de l'aim
    camera_rotation_grp = cmds.group(empty=True, name='Camera_Rotation_Grp')
    cmds.setAttr(f"{camera_rotation_grp}.translateX", aim_x)
    cmds.setAttr(f"{camera_rotation_grp}.translateY", aim_y)
    cmds.setAttr(f"{camera_rotation_grp}.translateZ", aim_z)
    
    # Parent la caméra au groupe de rotation
    cmds.parent(camera_transform, camera_rotation_grp)
    
    # Repositionne la caméra relativement au groupe
    rel_cam_x = cam_x - aim_x
    rel_cam_y = cam_y - aim_y
    rel_cam_z = cam_z - aim_z
    
    cmds.setAttr(f"{camera_transform}.translateX", rel_cam_x)
    cmds.setAttr(f"{camera_transform}.translateY", rel_cam_y)
    cmds.setAttr(f"{camera_transform}.translateZ", rel_cam_z)
    
    # Anime le groupe : 2 tours complets (720°) sur 120 frames
    cmds.setKeyframe(camera_rotation_grp, attribute='rotateY', time=0, value=0)
    cmds.setKeyframe(camera_rotation_grp, attribute='rotateY', time=120, value=720)
    
    # Définit l'interpolation en linéaire pour une rotation constante
    cmds.keyTangent(camera_rotation_grp, attribute='rotateY', inTangentType='linear', outTangentType='linear')
    
    print(f"Animation créée: 2 tours (720°) sur 120 frames")
    
    print(f"Caméra créée à la position: X={cam_x}, Y={cam_y}, Z={cam_z}")
    print(f"Aim créé à la position: X={aim_x}, Y={aim_y}, Z={aim_z}")
    
    print("=" * 50)
    print("Scène LookDev configurée!")
    print("Variables disponibles pour formules:")
    print(f"  - Centre: center_x, center_y, center_z")
    print(f"  - Taille: size_x, size_y, size_z")
    print("=" * 50)


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
    
    # Ajoute un bouton pour assigner des matériaux uniques
    cmds.shelfButton(
        parent=main_shelf,
        label="Materials",
        command="from customPlugins import assign_unique_materials\nassign_unique_materials()",
        image="render_aiStandardSurface.png",
        annotation="Assigner un matériau aiStandardSurface unique à chaque mesh",
        imageOverlayLabel="Mat",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour enlever le préfixe "pasted__"
    cmds.shelfButton(
        parent=main_shelf,
        label="Remove Pasted",
        command="from customPlugins import remove_pasted_prefix\nremove_pasted_prefix()",
        image="textEditing.png",
        annotation="Enlever le préfixe 'pasted__' de tous les objets",
        imageOverlayLabel="Paste",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour supprimer les groupes vides
    cmds.shelfButton(
        parent=main_shelf,
        label="Delete Empty",
        command="from customPlugins import delete_empty_groups\ndelete_empty_groups()",
        image="deleteActive.png",
        annotation="Supprimer tous les groupes vides",
        imageOverlayLabel="DelE",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour configurer Arnold
    cmds.shelfButton(
        parent=main_shelf,
        label="Arnold Setup",
        command="from customPlugins import setup_arnold_render\nsetup_arnold_render()",
        image="render_arnold.png",
        annotation="Configurer Arnold pour le compositing (1920x1080, EXR, AOVs)",
        imageOverlayLabel="Arnd",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour configurer la scène LookDev
    cmds.shelfButton(
        parent=main_shelf,
        label="LookDev Setup",
        command="from customPlugins import setup_lookdev_scene\nsetup_lookdev_scene()",
        image="camera.svg",
        annotation="Configurer scène LookDev (Arnold + HDRI + Caméra)",
        imageOverlayLabel="Look",
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