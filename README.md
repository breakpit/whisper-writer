# WhisperType

**Dictée vocale locale pour Windows** - Application minimaliste de transcription vocale utilisant Whisper, optimisée pour le français technique avec termes anglais.

Fork simplifié de [whisper-writer](https://github.com/savbell/whisper-writer).

## Fonctionnalités

- **100% Local** - Aucune API cloud, aucun coût de tokens, confidentialité totale
- **Hotkey Global** - `Ctrl+Space` pour démarrer/arrêter l'enregistrement (configurable)
- **Feedback Audio** - Sons distincts pour début et fin d'enregistrement
- **Frappe Automatique** - Le texte s'écrit directement où se trouve le curseur
- **Interface Minimale** - Icône systray uniquement, pas de fenêtre intrusive
- **Français Technique** - Optimisé pour le mélange français/anglais (API, Docker, Kubernetes, etc.)

## Installation

### Prérequis

- Windows 10/11 (64-bit)
- Python 3.10+
- GPU NVIDIA avec CUDA (recommandé) ou CPU

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Téléchargement du modèle

Au premier lancement, le modèle Whisper sera téléchargé automatiquement (~3GB pour large-v3).

## Utilisation

### Lancement

```bash
python run.py
```

L'icône WhisperType apparaît dans la barre système.

### Dictée

1. Placez votre curseur où vous voulez écrire
2. Appuyez sur `Ctrl+Space` - Son de début
3. Dictez votre texte
4. Appuyez sur `Ctrl+Space` - Son de fin + transcription
5. Le texte s'écrit automatiquement à la position du curseur

### Menu Systray

- **Clic droit** - Menu contextuel
  - `Open Config` - Ouvrir le fichier de configuration
  - `Quit` - Quitter l'application

## Configuration

Éditez `src/config.yaml` pour personnaliser :

```yaml
# Raccourci clavier
recording_options:
  activation_key: ctrl+space  # Changez pour alt+space, ctrl+shift+space, etc.

# Modèle Whisper
model_options:
  local:
    model: medium  # ou large-v3, small, base, tiny
    device: auto     # cuda, cpu, ou auto

# Sortie
output:
  copy_to_clipboard: false  # Copie dans presse-papiers
  auto_type: true           # Frappe automatique (activé par défaut)

# Sons
misc:
  noise_on_start: true      # Son de début
  noise_on_completion: true # Son de fin
```

## Modèles disponibles

| Modèle | Taille | RAM GPU | Précision |
|--------|--------|---------|-----------|
| tiny | ~75MB | ~1GB | Faible |
| base | ~140MB | ~1GB | Moyenne |
| small | ~460MB | ~2GB | Bonne |
| medium | ~1.5GB | ~5GB | Très bonne |
| large-v3 | ~3GB | ~10GB | Excellente |

Pour le français technique avec termes anglais, `large-v3` ou `medium` sont recommandés.

## Dépannage

### Pas de son au démarrage
Vérifiez que `assets/start.wav` et `assets/beep.wav` existent.

### Hotkey ne fonctionne pas
- Vérifiez qu'aucune autre application n'utilise `Ctrl+Space`
- Essayez un autre raccourci dans `config.yaml`

### Transcription lente
- Utilisez un modèle plus petit (medium, small)
- Activez CUDA si vous avez un GPU NVIDIA

### Erreur CUDA
Installez CUDA Toolkit et cuDNN, ou forcez le mode CPU :
```yaml
model_options:
  local:
    device: cpu
    compute_type: int8
```

## Licence

GPL-3.0 - Voir [LICENSE](LICENSE)

## Crédits

- [whisper-writer](https://github.com/savbell/whisper-writer) - Projet original
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Implémentation optimisée de Whisper
- [OpenAI Whisper](https://github.com/openai/whisper) - Modèle de transcription
