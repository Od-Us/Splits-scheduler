# Programmation des splits (intégration Home Assistant)

Intégration personnalisée `split_scheduler` qui programme les splits d'une pompe
à chaleur exposés comme thermostats (`climate.*`), par exemple via Faikout et MQTT.

- **Groupes** : un groupe contient un ou plusieurs splits.
- **Profils** : réglages préenregistrés (mode, consigne, vitesse du ventilateur,
  oscillations) applicables à n'importe quel groupe.
- **Plannings** : plusieurs types de semaine (Normal, Vacances, Absence
  prolongée…). Chaque planning contient, pour chaque groupe, un programme
  hebdomadaire des changements de profil.
- Un **sélecteur de planning** par groupe, plus un sélecteur global qui bascule
  tous les groupes d'un coup.
- Un **réglage manuel** (télécommande, thermostat HA, choix d'un profil) est
  respecté jusqu'au prochain créneau programmé.

Tout se configure depuis l'interface de Home Assistant, sans YAML.

## Installation

1. Copier le dossier `custom_components/split_scheduler` dans le dossier
   `config/custom_components/` de Home Assistant (via Samba, File editor,
   Studio Code Server…).
2. Redémarrer Home Assistant.
3. *Paramètres → Appareils et services → Ajouter une intégration →
   « Programmation des splits »*.

Home Assistant 2024.12 ou plus récent est nécessaire. Vérifié sur Home Assistant OS
avec Core **2026.11.0** (Python 3.14).

À l'installation, des profils et des plannings sont créés d'office ; ils sont
tous modifiables ou supprimables :

| Profil          | Mode      | Consigne |
|-----------------|-----------|----------|
| Hors gel        | Chauffage | 10 °C    |
| Eco             | Chauffage | 18 °C    |
| Eco absence     | Chauffage | 16 °C    |
| Confort         | Chauffage | 20 °C    |
| Confort absence | Chauffage | 19 °C    |
| Boost           | Chauffage | 23 °C    |
| Arrêt           | Arrêt     | –        |
| Manuel          | –         | –        |

Plannings fournis : *Normal*, *Vacances*, *Absence prolongée* (vides au départ).

## Configuration

Sur la carte de l'intégration, cliquer sur **Configurer**. Un menu propose :

- **Groupes de splits** : nom et thermostats du groupe.
- **Profils de fonctionnement** : un champ laissé vide n'est *pas modifié* sur
  les splits. Par exemple, un profil qui ne fixe que la consigne garde le mode
  en cours. Les vitesses de ventilateur et les oscillations proposées sont
  celles que vos splits annoncent (`fan_modes`, `swing_modes`…) ; on peut aussi
  saisir une valeur.
- **Types de planning** : ajout (éventuellement en copiant les programmes d'un
  planning existant), renommage, suppression.
- **Programme hebdomadaire d'un groupe** : choisir un planning et un groupe,
  puis saisir chaque jour sous la forme

  ```
  06:30 Confort, 08:30 Eco, 18:00 Confort, 22:30 Eco
  ```

  Les formats `6h30`, `7h` et `7` sont acceptés, et la casse comme les accents
  des noms de profil sont ignorés. La case *Recopier le lundi sur* évite de
  ressaisir les jours identiques.

**Pensez à « Enregistrer et fermer »** : les modifications ne sont appliquées
qu'à ce moment-là, et l'intégration se recharge.

### Comment un programme est lu

Chaque créneau indique *à partir de quand* un profil s'applique. Le profil
reste actif jusqu'au créneau suivant, même s'il tombe un autre jour. Un jour
sans créneau prolonge donc le dernier profil de la veille. Exemple pour le
planning *Absence prolongée* : saisir seulement `00:00 Hors gel` le lundi suffit
à maintenir le hors-gel toute la semaine.

Un groupe sans programme dans le planning choisi n'est jamais modifié
automatiquement (statut *Aucun programme*).

## Entités créées

Pour chaque groupe (un appareil par groupe) :

| Entité | Rôle |
|---|---|
| `select.<groupe>_profil` | Profil actif. Choisir un profil l'applique tout de suite, jusqu'au prochain créneau. Attributs : `profil_programme`, `derogation`, `splits`. |
| `select.<groupe>_planning` | Planning suivi par le groupe. Le changer applique aussitôt le profil du créneau en cours. |
| `switch.<groupe>_programmation` | Éteint : plus aucun changement automatique. Rallumé : le profil programmé est réappliqué. |
| `button.<groupe>_reprendre_la_programmation` | Annule une dérogation et réapplique le profil programmé. |
| `sensor.<groupe>_statut` | `Programmé`, `Dérogation`, `Programmation désactivée` ou `Aucun programme`. |
| `sensor.<groupe>_prochain_changement` | Date du prochain changement ; attribut `prochain_profil`. |

Et une entité globale : `select.programmation_des_splits_planning_de_tous_les_groupes`.
Elle affiche le planning commun à tous les groupes, ou *inconnu* s'ils diffèrent.

Les identifiants exacts dépendent de la langue de Home Assistant lors de la
création des entités ; ils se retrouvent dans la page de l'appareil.

## Comportement en détail

- **Réglage manuel** : si un split s'écarte du profil appliqué (mode,
  consigne à plus de 0,3 °C près, ventilateur, oscillation) plus de 2 minutes
  après l'envoi, le groupe passe en *Dérogation*. Rien n'est réimposé avant le
  prochain créneau, ou avant un appui sur *Reprendre la programmation*.
- **Redémarrage de Home Assistant** : un changement prévu pendant l'arrêt est
  rattrapé au démarrage. Une dérogation en cours dans le même créneau est
  conservée.
- **Split indisponible** (Wi-Fi, MQTT) : le profil est mis en attente et envoyé
  dès que le split redevient disponible.
- **Commandes envoyées** : seules les valeurs qui diffèrent de l'état actuel sont
  envoyées. La consigne est bornée aux limites du split : un hors-gel à 8 °C
  devient 16 °C sur un Faikout S21. La consigne est aussi arrondie au pas du
  split (0,5 °C). Une valeur que le split ne
  gère pas est ignorée et signalée dans le journal.

## Exemples d'automatisations

Passer toute la maison en *Absence prolongée* quand tout le monde est parti
depuis 24 h, puis revenir en *Normal* au retour :

```yaml
automation:
  - alias: Splits - absence prolongée
    triggers:
      - trigger: state
        entity_id: zone.home
        to: "0"
        for: "24:00:00"
    actions:
      - action: select.select_option
        target:
          entity_id: select.programmation_des_splits_planning_de_tous_les_groupes
        data:
          option: Absence prolongée

  - alias: Splits - retour à la maison
    triggers:
      - trigger: numeric_state
        entity_id: zone.home
        above: 0
    actions:
      - action: select.select_option
        target:
          entity_id: select.programmation_des_splits_planning_de_tous_les_groupes
        data:
          option: Normal
```

Boost d'une heure dans le salon (le programme reprend ensuite la main) :

```yaml
script:
  boost_salon:
    sequence:
      - action: select.select_option
        target: { entity_id: select.salon_profil }
        data: { option: Boost }
      - delay: "01:00:00"
      - action: button.press
        target: { entity_id: button.salon_reprendre_la_programmation }
```

## Carte de tableau de bord

```yaml
type: entities
title: Salon
entities:
  - select.salon_profil
  - select.salon_planning
  - sensor.salon_statut
  - sensor.salon_prochain_changement
  - switch.salon_programmation
  - button.salon_reprendre_la_programmation
```

## Splits Faikout (MQTT)

Vérifié avec les attributs d'un Faikout en port **S21** et
d'après le code source de Faikout (découverte MQTT de Home Assistant).

| Réglage | Valeurs Faikout | Remarque |
|---|---|---|
| Mode | `heat_cool`, `off`, `cool`, `heat`, `dry`, `fan_only` | Pas de `auto` : choisir « Chaud / froid » (`heat_cool`). Le formulaire ne propose que les modes annoncés. |
| Consigne | 16 à 32 °C, pas de 0,5 °C | **Le profil « Hors gel » (10 °C) est ramené à 16 °C**, comme « Eco absence ». Pour un vrai hors-gel plus bas, il n'y a pas d'autre moyen que le mode Arrêt. |
| Ventilateur | `auto`, `night`, `low`, `lowMedium`, `medium`, `mediumHigh`, `high` | Proposés tels quels dans le formulaire. |
| Oscillation | `off`, `H`, `V`, `H+V` | Une seule valeur pour les deux axes : laisser vide « Oscillation horizontale ». |
| Préréglage | `none`, `boost`, `home` | Jamais modifié par l'intégration : le split reste sur `home`. |

**Désactiver l'option « Auto » (`autoe`) de Faikout** sur les splits programmés :
sinon le module change lui-même de mode et de consigne, et l'intégration
prend ces changements pour des réglages manuels.

## Astuce : été / hiver

Un profil fixe un seul mode. Pour la climatisation, créez par exemple des
profils *Confort été* (Climatisation, 26 °C) et *Eco été*, et un planning *Été*
qui les utilise. Le passage d'une saison à l'autre se fait alors avec le
sélecteur de planning global.

## Tests

Python 3.14 est nécessaire (comme Home Assistant 2026.x) :

```bash
cd home_assistant
pip install pytest-homeassistant-custom-component
pytest
```

`pytest-homeassistant-custom-component` suit Home Assistant avec un peu de
retard. Sa version 0.13.375 embarque Core 2026.10.4 et ne fonctionne pas encore
avec Core 2026.11 : la compatibilité 2026.11.0 a donc été vérifiée sur un vrai
serveur Home Assistant.
