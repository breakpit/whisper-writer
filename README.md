# WhisperType

**Dictée vocale locale pour Windows** - Application minimaliste de transcription vocale utilisant Whisper, optimisée pour le français technique avec termes anglais.

Fork simplifié de [whisper-writer](https://github.com/savbell/whisper-writer).

## Fonctionnalités

- **100% Local** - Aucune API cloud, aucun coût de tokens, confidentialité totale
- **Hotkey Global** - `Alt+Space` pour démarrer/arrêter l'enregistrement (configurable)
- **Feedback Audio** - Sons distincts pour début et fin d'enregistrement
- **Copie Automatique** - Texte transcrit copié dans le presse-papiers
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

1. Appuyez sur `Alt+Space` - Son de début
2. Dictez votre texte
3. Appuyez sur `Alt+Space` - Son de fin + transcription
4. Le texte est copié dans le presse-papiers
5. Collez avec `Ctrl+V`

### Menu Systray

- **Clic droit** - Menu contextuel
  - `Open Config` - Ouvrir le fichier de configuration
  - `Quit` - Quitter l'application

## Configuration

Éditez `src/config.yaml` pour personnaliser :

```yaml
# Raccourci clavier
recording_options:
  activation_key: alt+space  # Changez pour ctrl+shift+space, etc.

# Modèle Whisper
model_options:
  local:
    model: large-v3  # ou medium, small, base, tiny
    device: auto     # cuda, cpu, ou auto

# Sortie
output:
  copy_to_clipboard: true   # Copie automatique
  auto_type: false          # Frappe automatique (désactivé par défaut)

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
- Vérifiez qu'aucune autre application n'utilise `Alt+Space`
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
