# Custom Maya Plugin - MesOutils

Un plugin Maya personnalisé qui ajoute un shelf d'outils pour optimiser votre workflow de modélisation, lookdev et rendu Arnold.

## Installation

### Méthode 1 : Installation manuelle

1. Copiez le fichier `customPlugins.py` dans le dossier plug-ins de Maya :
   - **Windows** : `C:\Users\<username>\Documents\maya\<version>\plug-ins\`
   - **macOS** : `/Users/<username>/Library/Preferences/Autodesk/maya/<version>/plug-ins/`
   - **Linux** : `/home/<username>/maya/<version>/plug-ins/`

2. Ouvrez Maya

3. Allez dans **Window > Settings/Preferences > Plug-in Manager**

4. Trouvez `customPlugins.py` dans la liste et cochez **Loaded** et **Auto load**

5. Le shelf "MesOutils" apparaîtra automatiquement

### Méthode 2 : Chargement via Script Editor

1. Ouvrez le **Script Editor** (`Window > General Editors > Script Editor`)

2. Dans l'onglet Python, exécutez :
```python
import maya.cmds as cmds
cmds.loadPlugin("chemin/vers/customPlugins.py")
```

## Fonctionnalités

### Utilitaires Mesh

| Bouton | Fonction | Description |
|--------|----------|-------------|
| **Del History** | `delete_history()` | Supprime l'historique de construction des mesh sélectionnés |
| **Freeze** | `freeze_transform()` | Gèle les transformations (translate, rotate, scale) des mesh sélectionnés |
| **Materials** | `assign_unique_materials()` | Assigne un matériau aiStandardSurface unique à chaque mesh sélectionné |

### Nettoyage de scène

| Bouton | Fonction | Description |
|--------|----------|-------------|
| **Remove Pasted** | `remove_pasted_prefix()` | Enlève le préfixe "pasted__" de tous les objets (après copier-coller) |
| **Delete Empty** | `delete_empty_groups()` | Supprime tous les groupes vides de la scène (récursif) |
| **Delete Unknown** | `delete_unknown_nodes()` | Supprime les nodes inconnus (souvent après import de fichiers externes) |
| **Delete Unused** | `delete_unused_nodes()` | Supprime les matériaux, textures et nodes inutilisés |

### Renommage

| Bouton | Fonction | Description |
|--------|----------|-------------|
| **Batch Rename** | `batch_rename()` | Ouvre une fenêtre pour renommer plusieurs objets avec préfixe, suffixe, ou rechercher/remplacer |

**Utilisation du Batch Rename :**
1. Sélectionnez les objets à renommer
2. Cliquez sur le bouton "Batch Rename"
3. Remplissez les champs souhaités :
   - **Préfixe** : texte ajouté au début (ex: `prop_`)
   - **Suffixe** : texte ajouté à la fin (ex: `_geo`)
   - **Rechercher/Remplacer** : remplace un texte par un autre
4. Cliquez sur "Appliquer"

### Configuration Arnold

| Bouton | Fonction | Description |
|--------|----------|-------------|
| **Arnold Setup** | `setup_arnold_render()` | Configure Arnold pour le compositing |

**Paramètres configurés :**
- Résolution : 1920x1080
- Format : EXR avec Merge AOVs
- Frames : 0-120
- GPU activé (Windows uniquement)
- AOVs : RGBA, diffuse, specular, transmission, sss, emission, volume, N, Z, crypto_asset, crypto_object, crypto_material

### LookDev

| Bouton | Fonction | Description |
|--------|----------|-------------|
| **LookDev Setup** | `setup_lookdev_scene()` | Configure une scène lookdev complète et lance le rendu |
| **Clean LookDev** | `clean_lookdev()` | Nettoie la scène après le rendu (supprime le setup, réaffiche les objets) |

**Workflow LookDev :**
1. Sélectionnez l'objet ou groupe à rendre
2. Cliquez sur **LookDev Setup**
3. Le script va :
   - Configurer Arnold (via `setup_arnold_render()`)
   - Masquer tous les autres objets de la scène
   - Créer un HDRI skydome (sauf s'il existe déjà)
   - Créer une caméra avec turntable 360° sur 120 frames
   - Positionner la caméra automatiquement selon la taille de l'objet
   - Lancer un Batch Render
4. Une fois le rendu terminé, cliquez sur **Clean LookDev** pour :
   - Supprimer le groupe LookDev_Setup_GRP
   - Réafficher les objets masqués
   - Conserver l'HDRI s'il existait avant

### Export

| Bouton | Fonction | Description |
|--------|----------|-------------|
| **FBX Export** | `quick_fbx_export()` | Ouvre la fenêtre d'export FBX avec options |
| **USD Export** | `quick_usd_export()` | Ouvre la fenêtre d'export USD avec options |

### Sélection

| Bouton | Fonction | Description |
|--------|----------|-------------|
| **Select by Type** | `select_by_type()` | Ouvre une fenêtre pour sélectionner des objets par type |

**Types disponibles :**
- Meshes
- Curves
- Surfaces NURBS
- Joints
- Locators
- Cameras (hors caméras par défaut)
- Lights Maya
- Arnold Lights

## Prérequis

- Maya 2022 ou supérieur
- Arnold for Maya (mtoa) pour les fonctionnalités de rendu
- mayaUsdPlugin pour l'export USD (optionnel)

## Structure du shelf

Le shelf "MesOutils" est créé automatiquement au chargement du plugin avec tous les boutons organisés dans l'ordre suivant :

1. Del History
2. Freeze
3. Materials
4. Remove Pasted
5. Delete Empty
6. Arnold Setup
7. LookDev Setup
8. Clean LookDev
9. Delete Unknown
10. Delete Unused
11. Batch Rename
12. FBX Export
13. USD Export
14. Select by Type

## Dépannage

### Le shelf n'apparaît pas
- Vérifiez que le plugin est bien chargé dans le Plug-in Manager
- Essayez de recharger le plugin

### Erreur "mtoa not found"
- Assurez-vous qu'Arnold for Maya est installé et chargé

### Le Batch Render ne se lance pas
- Vérifiez les Render Settings (chemin de sortie, format, etc.)
- Consultez le Script Editor pour les messages d'erreur

## Auteur

Plugin développé pour optimiser le workflow Maya.

## Licence

Libre d'utilisation et de modification.
