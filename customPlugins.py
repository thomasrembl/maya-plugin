import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaMPx as ommpx
import sys
import os


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


def delete_unknown_nodes():
    """Supprime tous les nodes inconnus dans la scène"""
    unknown_nodes = cmds.ls(type='unknown') or []
    unknown_dag = cmds.ls(type='unknownDag') or []
    
    all_unknown = unknown_nodes + unknown_dag
    deleted_count = 0
    
    for node in all_unknown:
        try:
            # Déverrouille le node si nécessaire
            if cmds.lockNode(node, query=True, lock=True)[0]:
                cmds.lockNode(node, lock=False)
            cmds.delete(node)
            deleted_count += 1
            print(f"Node inconnu supprimé: '{node}'")
        except Exception as e:
            print(f"Impossible de supprimer '{node}': {str(e)}")
    
    if deleted_count > 0:
        print(f"{deleted_count} node(s) inconnu(s) supprimé(s)")
    else:
        print("Aucun node inconnu trouvé")


def delete_unused_nodes():
    """Supprime tous les nodes inutilisés (materials, textures, etc.)"""
    
    # Utilise MEL pour optimiser la scène (supprime les nodes inutilisés)
    import maya.mel as mel
    
    deleted_counts = {}
    
    # Types de nodes à vérifier
    node_types = [
        ('shadingEngine', 'Shading Groups'),
        ('lambert', 'Lambert'),
        ('blinn', 'Blinn'),
        ('phong', 'Phong'),
        ('aiStandardSurface', 'aiStandardSurface'),
        ('file', 'File Textures'),
        ('place2dTexture', 'Place2D Textures'),
        ('bump2d', 'Bump2D'),
        ('multiplyDivide', 'MultiplyDivide'),
        ('ramp', 'Ramp'),
        ('noise', 'Noise'),
        ('layeredTexture', 'Layered Textures'),
    ]
    
    # Compte les nodes avant
    before_counts = {}
    for node_type, _ in node_types:
        try:
            before_counts[node_type] = len(cmds.ls(type=node_type) or [])
        except:
            before_counts[node_type] = 0
    
    # Utilise la commande MLdeleteUnused pour supprimer les nodes inutilisés
    try:
        mel.eval('MLdeleteUnused;')
    except:
        # Fallback: suppression manuelle
        mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')
    
    # Compte les nodes après
    total_deleted = 0
    for node_type, label in node_types:
        try:
            after_count = len(cmds.ls(type=node_type) or [])
            deleted = before_counts[node_type] - after_count
            if deleted > 0:
                deleted_counts[label] = deleted
                total_deleted += deleted
        except:
            pass
    
    # Affiche le résumé
    print("=" * 50)
    if total_deleted > 0:
        print(f"Nodes inutilisés supprimés: {total_deleted}")
        for label, count in deleted_counts.items():
            print(f"  - {label}: {count}")
    else:
        print("Aucun node inutilisé trouvé")
    print("=" * 50)


def batch_rename():
    """Ouvre une fenêtre pour renommer plusieurs objets avec préfixe/suffixe"""
    
    window_name = "batchRenameWindow"
    
    # Ferme la fenêtre si elle existe déjà
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)
    
    # Crée la fenêtre
    window = cmds.window(window_name, title="Batch Rename", widthHeight=(300, 280), sizeable=True)
    
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnOffset=('both', 10))
    
    cmds.separator(height=10, style='none')
    
    # Champ pour le préfixe
    cmds.text(label="Préfixe:", align='left')
    prefix_field = cmds.textField("batchRenamePrefix", placeholderText="ex: prop_")
    
    # Champ pour le suffixe
    cmds.text(label="Suffixe:", align='left')
    suffix_field = cmds.textField("batchRenameSuffix", placeholderText="ex: _geo")
    
    # Champ pour rechercher/remplacer
    cmds.text(label="Rechercher:", align='left')
    search_field = cmds.textField("batchRenameSearch", placeholderText="texte à rechercher")
    
    cmds.text(label="Remplacer par:", align='left')
    replace_field = cmds.textField("batchRenameReplace", placeholderText="texte de remplacement")
    
    cmds.separator(height=10, style='none')
    
    # Bouton pour appliquer
    cmds.button(label="Appliquer", command=lambda x: apply_batch_rename(), height=30)
    
    cmds.showWindow(window)


def apply_batch_rename():
    """Applique le renommage batch"""
    
    selection = cmds.ls(sl=True)
    if not selection:
        cmds.warning("Aucune sélection ! Veuillez sélectionner des objets.")
        return
    
    prefix = cmds.textField("batchRenamePrefix", query=True, text=True)
    suffix = cmds.textField("batchRenameSuffix", query=True, text=True)
    search = cmds.textField("batchRenameSearch", query=True, text=True)
    replace = cmds.textField("batchRenameReplace", query=True, text=True)
    
    renamed_count = 0
    
    for obj in selection:
        short_name = obj.split('|')[-1]
        new_name = short_name
        
        # Rechercher/Remplacer
        if search:
            new_name = new_name.replace(search, replace)
        
        # Ajoute préfixe et suffixe
        new_name = prefix + new_name + suffix
        
        # Renomme seulement si le nom change
        if new_name != short_name:
            try:
                cmds.rename(obj, new_name)
                renamed_count += 1
                print(f"Renommé: '{short_name}' -> '{new_name}'")
            except Exception as e:
                print(f"Impossible de renommer '{short_name}': {str(e)}")
    
    print(f"{renamed_count} objet(s) renommé(s)")


def quick_fbx_export():
    """Ouvre la fenêtre d'export FBX avec options"""
    
    import maya.mel as mel
    
    # Charge le plugin FBX si nécessaire
    if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
        try:
            cmds.loadPlugin("fbxmaya")
        except:
            cmds.error("Impossible de charger le plugin FBX")
            return
    
    # Définit FBX comme type d'export et ouvre le dialogue avec options
    cmds.optionVar(sv=("defaultFileExportActiveType", "FBX export"))
    mel.eval('ExportSelectionOptions')


def quick_usd_export():
    """Ouvre la fenêtre d'export USD avec options"""
    
    import maya.mel as mel
    
    # Charge le plugin USD si nécessaire
    if not cmds.pluginInfo("mayaUsdPlugin", query=True, loaded=True):
        try:
            cmds.loadPlugin("mayaUsdPlugin")
        except:
            cmds.error("Impossible de charger le plugin USD (mayaUsdPlugin)")
            return
    
    # Définit USD comme type d'export et ouvre le dialogue avec options
    cmds.optionVar(sv=("defaultFileExportActiveType", "USD Export"))
    mel.eval('ExportSelectionOptions')


def select_by_type():
    """Ouvre une fenêtre pour sélectionner des objets par type"""
    
    window_name = "selectByTypeWindow"
    
    # Ferme la fenêtre si elle existe déjà
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)
    
    # Crée la fenêtre
    window = cmds.window(window_name, title="Select by Type", widthHeight=(250, 320), sizeable=True)
    
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=('both', 10))
    
    cmds.separator(height=10, style='none')
    cmds.text(label="Sélectionner par type:", align='left', font='boldLabelFont')
    cmds.separator(height=10, style='none')
    
    # Boutons pour chaque type
    cmds.button(label="Meshes", command=lambda x: select_type('mesh'), height=25)
    cmds.button(label="Curves", command=lambda x: select_type('nurbsCurve'), height=25)
    cmds.button(label="Surfaces NURBS", command=lambda x: select_type('nurbsSurface'), height=25)
    cmds.button(label="Joints", command=lambda x: select_type('joint'), height=25)
    cmds.button(label="Locators", command=lambda x: select_type('locator'), height=25)
    cmds.button(label="Cameras", command=lambda x: select_type('camera'), height=25)
    cmds.button(label="Lights", command=lambda x: select_type('light'), height=25)
    cmds.button(label="Arnold Lights", command=lambda x: select_type('aiLight'), height=25)
    
    cmds.separator(height=10, style='none')
    
    cmds.showWindow(window)


def select_type(node_type):
    """Sélectionne tous les objets d'un type donné"""
    
    if node_type == 'light':
        # Sélectionne toutes les lights Maya standard
        lights = cmds.ls(type=['ambientLight', 'directionalLight', 'pointLight', 'spotLight', 'areaLight', 'volumeLight'])
        transforms = []
        for light in lights:
            parent = cmds.listRelatives(light, parent=True)
            if parent:
                transforms.append(parent[0])
        if transforms:
            cmds.select(transforms, replace=True)
            print(f"{len(transforms)} light(s) sélectionnée(s)")
        else:
            cmds.select(clear=True)
            print("Aucune light trouvée")
    
    elif node_type == 'aiLight':
        # Sélectionne toutes les lights Arnold
        ai_lights = cmds.ls(type=['aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight', 'aiPhotometricLight', 'aiLightPortal'])
        transforms = []
        for light in ai_lights:
            parent = cmds.listRelatives(light, parent=True)
            if parent:
                transforms.append(parent[0])
        if transforms:
            cmds.select(transforms, replace=True)
            print(f"{len(transforms)} Arnold light(s) sélectionnée(s)")
        else:
            cmds.select(clear=True)
            print("Aucune Arnold light trouvée")
    
    elif node_type == 'camera':
        # Sélectionne les caméras (sauf les caméras par défaut)
        cameras = cmds.ls(type='camera')
        default_cameras = ['perspShape', 'topShape', 'frontShape', 'sideShape']
        transforms = []
        for cam in cameras:
            if cam not in default_cameras:
                parent = cmds.listRelatives(cam, parent=True)
                if parent:
                    transforms.append(parent[0])
        if transforms:
            cmds.select(transforms, replace=True)
            print(f"{len(transforms)} caméra(s) sélectionnée(s)")
        else:
            cmds.select(clear=True)
            print("Aucune caméra trouvée (hors caméras par défaut)")
    
    else:
        # Sélectionne par type standard
        shapes = cmds.ls(type=node_type)
        transforms = []
        for shape in shapes:
            parent = cmds.listRelatives(shape, parent=True)
            if parent:
                transforms.append(parent[0])
        
        # Déduplique
        transforms = list(set(transforms))
        
        if transforms:
            cmds.select(transforms, replace=True)
            print(f"{len(transforms)} {node_type}(s) sélectionné(s)")
        else:
            cmds.select(clear=True)
            print(f"Aucun {node_type} trouvé")


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
    
    # Crée ou récupère le driver Arnold pour EXR
    drivers = cmds.ls(type='aiAOVDriver')
    exr_driver = None
    
    for driver in drivers:
        if cmds.getAttr(f"{driver}.aiTranslator") == "exr":
            exr_driver = driver
            break
    
    if not exr_driver:
        exr_driver = cmds.createNode('aiAOVDriver', name='defaultArnoldDriver')
        cmds.setAttr(f"{exr_driver}.aiTranslator", "exr", type="string")
    
    # Merge AOVs activé
    cmds.setAttr(f"{exr_driver}.mergeAOVs", 1)
    
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
    
    # Calcul du centre et de la taille
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    
    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    
    # Récupère tous les descendants de la sélection (pour ne pas les masquer)
    # Utilise les chemins longs pour éviter les problèmes de comparaison
    selection_long = cmds.ls(selection, long=True)
    selection_and_children = set(selection_long)
    
    for obj in selection_long:
        descendants = cmds.listRelatives(obj, allDescendents=True, fullPath=True) or []
        selection_and_children.update(descendants)
    
    # Masque tout sauf la sélection et ses enfants
    all_objects = cmds.ls(dag=True, visible=True, transforms=True, long=True)
    hidden_objects = []
    for obj in all_objects:
        if obj not in selection_and_children and cmds.objExists(obj):
            try:
                cmds.setAttr(f"{obj}.visibility", 0)
                hidden_objects.append(obj)
            except:
                pass
    
    # Vérifie si l'HDRI existait déjà AVANT de créer le groupe
    hdri_existed = cmds.objExists('lookdev_hdri')
    
    # Crée un groupe principal pour la scène LookDev
    lookdev_grp = cmds.group(empty=True, name='LookDev_Setup_GRP')
    
    # Stocke les infos pour le cleanup (attributs custom sur le groupe)
    cmds.addAttr(lookdev_grp, longName='hiddenObjects', dataType='string')
    cmds.setAttr(f"{lookdev_grp}.hiddenObjects", ','.join(hidden_objects), type='string')
    cmds.addAttr(lookdev_grp, longName='hdriExisted', attributeType='bool')
    cmds.setAttr(f"{lookdev_grp}.hdriExisted", hdri_existed)
    
    # Vérifie si un skydome "lookdev_hdri" existe déjà dans l'outliner
    if cmds.objExists('lookdev_hdri'):
        skydome = None
        cmds.setAttr("lookdev_hdri.visibility", 1)
        print("HDRI existant trouvé: lookdev_hdri (réaffiché, non ajouté au groupe)")
    else:
        # Crée le skydome HDRI (asLight=True retourne le transform)
        skydome = cmds.shadingNode('aiSkyDomeLight', asLight=True)
        skydome = cmds.rename(skydome, 'lookdev_hdri')
        
        cmds.setAttr(f"{skydome}.translateX", center_x)
        cmds.setAttr(f"{skydome}.translateY", center_y)
        cmds.setAttr(f"{skydome}.translateZ", center_z)
        print(f"HDRI créé: {skydome}")
    
    # Crée la caméra
    camera = cmds.camera(name='LookDev_Camera')
    camera_transform = camera[0]
    camera_shape = camera[1]
    
    # Récupère les paramètres de la caméra pour calculer le FOV
    import math
    focal_length = cmds.getAttr(f"{camera_shape}.focalLength")
    h_aperture = cmds.getAttr(f"{camera_shape}.horizontalFilmAperture")  # en pouces
    v_aperture = cmds.getAttr(f"{camera_shape}.verticalFilmAperture")    # en pouces
    
    # Calcul des FOV en radians (conversion pouces -> mm avec * 25.4)
    fov_h = 2 * math.atan((h_aperture * 25.4) / (2 * focal_length))
    fov_v = 2 * math.atan((v_aperture * 25.4) / (2 * focal_length))
    
    # Calcul de la distance nécessaire pour voir l'objet en entier
    distance_for_width = (size_x / 2) / math.tan(fov_h / 2)
    distance_for_height = (size_y / 2) / math.tan(fov_v / 2)
    
    # On prend le max + la moitié de la profondeur + 100% de marge
    padding = 2
    camera_distance = max(distance_for_width, distance_for_height) * padding + (size_z / 2)
    
    # Position de la caméra (légère plongée basée sur la hauteur de l'objet)
    cam_x = center_x
    cam_y = center_y + (size_y * 0.3)  # 30% de la hauteur pour l'effet de plongée
    cam_z = center_z + camera_distance
    
    # Crée l'aim (locator) au centre
    aim = cmds.spaceLocator(name='Camera_Aim')[0]
    cmds.setAttr(f"{aim}.translateX", center_x)
    cmds.setAttr(f"{aim}.translateY", center_y)
    cmds.setAttr(f"{aim}.translateZ", center_z)
    
    cmds.setAttr(f"{camera_transform}.translateX", cam_x)
    cmds.setAttr(f"{camera_transform}.translateY", cam_y)
    cmds.setAttr(f"{camera_transform}.translateZ", cam_z)
    
    # Contrainte aim sur la caméra
    cmds.aimConstraint(aim, camera_transform, aimVector=[0, 0, -1], upVector=[0, 1, 0])
    
    # Crée un groupe pour faire tourner la caméra autour de l'aim
    camera_rotation_grp = cmds.group(empty=True, name='Camera_Rotation_Grp')
    cmds.setAttr(f"{camera_rotation_grp}.translateX", center_x)
    cmds.setAttr(f"{camera_rotation_grp}.translateY", center_y)
    cmds.setAttr(f"{camera_rotation_grp}.translateZ", center_z)
    
    # Parent la caméra au groupe de rotation
    cmds.parent(camera_transform, camera_rotation_grp)
    
    # Anime le groupe : 1 tour complet (360°) sur 120 frames
    cmds.setKeyframe(camera_rotation_grp, attribute='rotateY', time=0, value=0)
    cmds.setKeyframe(camera_rotation_grp, attribute='rotateY', time=120, value=360)
    cmds.keyTangent(camera_rotation_grp, attribute='rotateY', inTangentType='linear', outTangentType='linear')
    
    # Parent tout au groupe principal
    if skydome:
        cmds.parent(skydome, lookdev_grp)
    cmds.parent(aim, lookdev_grp)
    cmds.parent(camera_rotation_grp, lookdev_grp)
    
    # Résumé
    print("=" * 50)
    print("Scène LookDev configurée!")
    print(f"  - {len(hidden_objects)} objet(s) masqué(s)")
    print(f"  - Centre: ({center_x:.2f}, {center_y:.2f}, {center_z:.2f})")
    print(f"  - Taille: ({size_x:.2f}, {size_y:.2f}, {size_z:.2f})")
    print(f"  - Distance caméra: {camera_distance:.2f}")
    print(f"  - Caméra: turntable 360° sur 120 frames")
    print(f"  - Groupe: {lookdev_grp}")
    print("=" * 50)
    
    # Configure la caméra LookDev pour le rendu
    
    # Désactive TOUTES les caméras pour le rendu d'abord
    all_cameras = cmds.ls(type='camera')
    for cam in all_cameras:
        try:
            cmds.setAttr(f"{cam}.renderable", 0)
        except:
            pass
    
    # Active uniquement la caméra LookDev
    cmds.setAttr(f"{camera_shape}.renderable", 1)
    
    # Désactive tous les render layers sauf masterLayer
    for layer in cmds.ls(type='renderLayer'):
        if layer != 'defaultRenderLayer':
            try:
                cmds.setAttr(f"{layer}.renderable", 0)
            except:
                pass
    
    # Active le masterLayer
    cmds.setAttr("defaultRenderLayer.renderable", 1)
    
    print(f"Caméra de rendu configurée: {camera_transform}")
    
    # Lance le batch render
    import maya.mel as mel
    try:
        print("Lancement du BatchRender...")
        mel.eval('BatchRender')
        print("BatchRender lancé")
        print("Une fois terminé, cliquez sur 'Clean LookDev' pour nettoyer la scène")
    except:
        print("Impossible de lancer le Batch Render")


def clean_lookdev():
    """Nettoie la scène après un lookdev : supprime le setup et réaffiche les objets masqués"""
    
    # Vérifie si le groupe LookDev existe
    if not cmds.objExists('LookDev_Setup_GRP'):
        cmds.warning("Aucun setup LookDev trouvé (LookDev_Setup_GRP)")
        return
    
    lookdev_grp = 'LookDev_Setup_GRP'
    
    # Récupère les infos stockées
    hdri_existed = False
    hidden_objects = []
    
    try:
        hdri_existed = cmds.getAttr(f"{lookdev_grp}.hdriExisted")
    except:
        pass
    
    try:
        hidden_str = cmds.getAttr(f"{lookdev_grp}.hiddenObjects")
        if hidden_str:
            hidden_objects = hidden_str.split(',')
    except:
        pass
    
    # Si l'HDRI existait avant, on le sort du groupe avant de supprimer
    if hdri_existed and cmds.objExists('lookdev_hdri'):
        try:
            cmds.parent('lookdev_hdri', world=True)
            print("HDRI conservé (existait avant le lookdev)")
        except:
            pass
    
    # Supprime le groupe LookDev (et tout ce qu'il contient)
    try:
        cmds.delete(lookdev_grp)
        print(f"Groupe '{lookdev_grp}' supprimé")
    except Exception as e:
        print(f"Erreur lors de la suppression du groupe: {str(e)}")
    
    # Réaffiche les objets masqués
    shown_count = 0
    for obj in hidden_objects:
        if cmds.objExists(obj):
            try:
                cmds.setAttr(f"{obj}.visibility", 1)
                shown_count += 1
            except:
                pass
    
    print("=" * 50)
    print("Cleanup LookDev terminé!")
    print(f"  - {shown_count} objet(s) réaffiché(s)")
    if hdri_existed:
        print("  - HDRI conservé")
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
    
    # Ajoute un bouton pour supprimer l'historique
    cmds.shelfButton(
        parent=main_shelf,
        label="Del History",
        command="from customPlugins import delete_history\ndelete_history()",
        image="DeleteHistory.png",
        annotation="Supprimer l'historique des mesh sélectionnés",
        imageOverlayLabel="DelH",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour freeze transform
    cmds.shelfButton(
        parent=main_shelf,
        label="Freeze",
        command="from customPlugins import freeze_transform\nfreeze_transform()",
        image="FreezeTransform.png",
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
        image="quickRename.png",
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
        image="renderGlobals.png",
        annotation="Configurer Arnold pour le compositing (1920x1080, EXR, AOVs)",
        imageOverlayLabel="Arnd",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour configurer la scène LookDev
    cmds.shelfButton(
        parent=main_shelf,
        label="LookDev Setup",
        command="from customPlugins import setup_lookdev_scene\nsetup_lookdev_scene()",
        image="cameraAim.png",
        annotation="Configurer scène LookDev (Arnold + HDRI + Caméra)",
        imageOverlayLabel="Look",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour nettoyer après le LookDev
    cmds.shelfButton(
        parent=main_shelf,
        label="Clean LookDev",
        command="from customPlugins import clean_lookdev\nclean_lookdev()",
        image="brush.png",
        annotation="Nettoyer la scène après le LookDev (supprime le setup, réaffiche les objets)",
        imageOverlayLabel="Clean",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour supprimer les nodes inconnus
    cmds.shelfButton(
        parent=main_shelf,
        label="Delete Unknown",
        command="from customPlugins import delete_unknown_nodes\ndelete_unknown_nodes()",
        image="nodeGrapherRemoveNodes.png",
        annotation="Supprimer tous les nodes inconnus",
        imageOverlayLabel="Unk",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour supprimer les nodes inutilisés
    cmds.shelfButton(
        parent=main_shelf,
        label="Delete Unused",
        command="from customPlugins import delete_unused_nodes\ndelete_unused_nodes()",
        image="deleteClip.png",
        annotation="Supprimer les materials, textures et nodes inutilisés",
        imageOverlayLabel="Unus",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour le batch rename
    cmds.shelfButton(
        parent=main_shelf,
        label="Batch Rename",
        command="from customPlugins import batch_rename\nbatch_rename()",
        image="quickRename.png",
        annotation="Renommer plusieurs objets (préfixe/suffixe/rechercher-remplacer)",
        imageOverlayLabel="Ren",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour l'export FBX
    cmds.shelfButton(
        parent=main_shelf,
        label="FBX Export",
        command="from customPlugins import quick_fbx_export\nquick_fbx_export()",
        image="out_mesh.png",
        annotation="Export FBX rapide",
        imageOverlayLabel="FBX",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour l'export USD
    cmds.shelfButton(
        parent=main_shelf,
        label="USD Export",
        command="from customPlugins import quick_usd_export\nquick_usd_export()",
        image="publish.png",
        annotation="Export USD rapide",
        imageOverlayLabel="USD",
        style="iconOnly"
    )
    
    # Ajoute un bouton pour sélectionner par type
    cmds.shelfButton(
        parent=main_shelf,
        label="Select by Type",
        command="from customPlugins import select_by_type\nselect_by_type()",
        image="selectByType.png",
        annotation="Sélectionner des objets par type",
        imageOverlayLabel="Sel",
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