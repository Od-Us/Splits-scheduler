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

### Avec HACS (dépôt public)

1. *HACS → ⋮ → Dépôts personnalisés* : ajouter
   `https://github.com/Od-Us/Splits-scheduler`, catégorie **Intégration**.
2. Télécharger « Programmation des splits », puis redémarrer Home Assistant.
3. *Paramètres → Appareils et services → Ajouter une intégration →
   « Programmation des splits »*.

### À la main

1. Copier le dossier `custom_components/split_scheduler` de ce dépôt dans le
   dossier `config/custom_components/` de Home Assistant (via Samba, File
   editor, Studio Code Server…).
2. Redémarrer Home Assistant.
3. *Paramètres → Appareils et services → Ajouter une intégration →
   « Programmation des splits »*.

Testée sur Home Assistant Core 2026.10 et 2026.11 (Home Assistant OS).

**Après une mise à jour de l'intégration**, redémarrez Home Assistant puis
**rechargez la page** (Ctrl+F5, ou fermez complètement et rouvrez l'application
Companion). Sinon, l'interface garde les textes de l'ancienne version : les
nouveaux écrans s'affichent avec des libellés vides.

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
| Confort été     | Climatisation | 26 °C (écart ext. max 10 °C) |
| Eco été         | Climatisation | 28 °C (écart ext. max 10 °C) |
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
- **Programme hebdomadaire d'un groupe** : choisir un planning et un groupe.
  La semaine s'affiche jour par jour avec le résumé des changements ; un jour
  vide indique le profil hérité (« Aucun changement — Eco depuis samedi 23:00 »).
  - Dans un jour : choisir une ligne pour la **modifier** (heure, profil) ou la
    **supprimer**, ou **ajouter** une ligne. Les lignes sont toujours triées par
    heure : une ligne ajoutée à 12:00 s'insère d'elle-même entre 08:30 et 17:00.
    Chaque profil proposé affiche ses réglages (« Confort — Chauffage · 20 °C »).
  - *Copier ce jour vers d'autres jours*, *Vider la journée*.
  - *Saisie rapide (texte)* : tous les jours d'un coup, sous la forme
    `06:30 Confort, 08:30 Eco, 18:00 Confort, 22:30 Eco` (formats `6h30`, `7h`
    et `7` acceptés, casse et accents ignorés).

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

L'intégration fournit la carte **« Programmation des splits »**, chargée
automatiquement : *Modifier le tableau de bord → Ajouter une carte →
Programmation des splits*. Tout se règle dans son éditeur visuel :

- titre, choix du planning pour tous les groupes, frise du programme du jour ;
- les groupes affichés et leur ordre (boutons *Monter* / *Descendre*) ;
- pour chaque groupe :
  - **température ambiante affichée** : un capteur de la pièce, qui remplace la
    température mesurée par le split (souvent faussée) ; vide = celle du split ;
  - **capteurs supplémentaires** affichés sous l'état (humidité, CO₂…) ;
  - **partie « Modifier »** : choix du planning du groupe, choix d'un profil,
    réglages manuels proposés (consigne, ventilateur, oscillation, mode) ;
  - **frise du compresseur** (facultative) : sous la frise des profils, une
    bande fine montre les périodes de marche du compresseur aujourd'hui et un
    trait à chaque démarrage, avec leur nombre en légende ;
  - **courbes du jour** (facultatives) : température ambiante, consigne et/ou
    température extérieure, de 0 h à 24 h sur le même axe que les frises
    (60 px de haut). La
    température ambiante est celle du capteur choisi pour le groupe, sinon
    celle du split ; la consigne n'est pas tracée quand le split est arrêté.

Chaque groupe montre en permanence la **consigne** (en grand), le profil actif,
la température ambiante, le statut, la frise du jour et le prochain changement.
En dérogation, un bandeau indique l'heure de reprise et propose *Reprendre*.
Le bouton **Modifier** déplie le planning, les profils, les réglages manuels et
l'interrupteur de programmation. Un réglage manuel est envoyé à **tous les
splits du groupe** et vaut dérogation jusqu'au prochain créneau.

La carte suit le thème clair ou sombre de Home Assistant. Pour une page
« Chauffage » plein écran, mettez-la seule dans une vue de type *Panneau*.

Exemple en YAML (l'éditeur visuel écrit la même chose) :

```yaml
type: custom:split-scheduler-card
title: Chauffage
show_global_planning: true
show_timeline: true
groups:
  - group: 252897f9            # identifiant choisi dans l'éditeur
    temperature_entity: sensor.salon_temperature
    sensors: [sensor.salon_humidite]
    show_planning: true
    show_profiles: true
    manual: [temperature, fan_mode, swing_mode]
    compressor: [avg_24h, avg_profile]
    compressor_timeline: true
    chart: [ambient, setpoint, outdoor]   # courbes du jour, au choix
```

La frise du compresseur et la courbe lisent l'historique de Home Assistant
(intégration *Historique*, active par défaut) et se mettent à jour toutes les
5 minutes, plus en direct pour la valeur actuelle.

Sans liste `groups`, tous les groupes sont affichés avec les réglages par défaut.

## Consigne adaptée à la température extérieure

Par canicule (ou grand froid), une consigne habituelle peut être hors de portée
du split, qui tournerait alors à fond en permanence. Chaque profil peut fixer un
**écart maximal avec l'extérieur** :

- **climatisation** (et déshumidification) : la consigne ne descend jamais à
  plus de cet écart sous la température extérieure. *Confort été* (26 °C, écart
  10 °C) donne 29 °C quand il fait 39 °C dehors ;
- **chauffage** : la consigne ne monte jamais à plus de cet écart au-dessus de
  l'extérieur (vide par défaut) ;
- vide : pas d'adaptation.

La consigne obtenue est ensuite arrondie au pas du split et bornée à ses limites
(16–32 °C sur un Faikout S21).

**Capteur extérieur** : un seul pour tous les groupes, dans *Configurer →
Réglages généraux*. Vide, c'est le capteur « Outside » de Faikout (sonde de
l'unité extérieure), détecté automatiquement ; il peut être faussé quand l'unité
tourne, surtout en climatisation : un capteur à l'ombre ou une station météo est
plus fiable.

**Réactivité**, pour ménager le matériel :

- température extérieure lissée sur **60 minutes** (moyenne pondérée dans le
  temps ; les périodes d'indisponibilité sont ignorées) ;
- consigne renvoyée au plus **toutes les 30 minutes**, seulement si elle change
  d'au moins **0,5 °C** ;
- **aucune adaptation si un changement de profil est prévu dans moins de 30
  minutes** ;
- sans valeur extérieure valable pendant une heure : retour à la consigne du
  profil ;
- après un réglage manuel (carte, télécommande), plus d'adaptation jusqu'au
  prochain créneau.

Au changement de profil, la consigne adaptée est appliquée tout de suite. Le
sélecteur de profil porte les attributs `consigne_profil`, `consigne_appliquee`,
`ecart_max_exterieur`, `temperature_exterieure` et `adaptation_exterieure`.

Sur la carte : badge **Adaptée** à côté de la consigne, rappel de la consigne du
profil, pastille **Extérieur (moy. 1 h)** et bandeau explicatif ; la courbe du
jour peut aussi tracer la température extérieure.

Sur une installation existante, *Confort été* et *Eco été* sont ajoutés une
seule fois à la mise à jour (sauf si un profil du même nom existe déjà) ; un
profil supprimé ensuite n'est pas recréé.

## Démarrages du compresseur

> **Précaution :** tous les splits d'un groupe sont considérés comme reliés au
> **même compresseur** (même unité extérieure). Si ce n'est pas le cas, créez un
> groupe par unité extérieure : sinon les démarrages comptés seront faux.

Dans la configuration d'un groupe, le champ **Capteur du compresseur** indique le
capteur qui donne la fréquence (ou la vitesse) du compresseur. Laissé vide, il
est détecté automatiquement : c'est le capteur « Compressor » publié par
Faikout sur le même appareil que l'un des splits. Un démarrage est compté à
chaque passage de 0 à une valeur positive ; les valeurs indisponibles sont
ignorées.

Deux capteurs sont alors créés pour le groupe (en démarrages par heure) :

| Entité | Valeur |
|---|---|
| `sensor.<groupe>_demarrages_du_compresseur_par_heure_24_h` | moyenne sur les 24 dernières heures |
| `sensor.<groupe>_demarrages_du_compresseur_par_heure_profil_actuel` | moyenne depuis le dernier changement de profil |

Attributs : `demarrages` (nombre), `duree_h` (durée observée), `depuis`, et
`profil` pour le second. Si l'enregistreur (historique) est actif, les
démarrages déjà enregistrés sont repris à l'installation ; sinon la moyenne
porte sur la durée observée depuis l'installation (aucune valeur avant 5
minutes). Les démarrages sont conservés sur 7 jours au plus.

Sur la carte, l'option **Démarrages du compresseur par heure** de chaque groupe
affiche l'une ou l'autre moyenne, ou les deux, sous l'état (comme les capteurs
supplémentaires) : « Compresseur (24 h) 2,3 dém./h », « Compresseur depuis
Confort 1,5 dém./h ».

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
| Compresseur | capteur « Compressor » (Hz, ou tr/min avec l'option `hacomprpm`) | Détecté automatiquement pour compter les démarrages. |

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
pip install pytest-homeassistant-custom-component
pytest
```

`pytest-homeassistant-custom-component` suit Home Assistant avec un peu de
retard. Sa version 0.13.375 embarque Core 2026.10.4 et ne fonctionne pas encore
avec Core 2026.11 : la compatibilité 2026.11.0 a donc été vérifiée sur un vrai
serveur Home Assistant.

## Licence

Copyright (C) 2026 Od-Us

Ce programme est un logiciel libre, distribué sous licence
[GNU GPL version 3](LICENSE) (GPL-3.0-only) : vous pouvez l'utiliser, l'étudier,
le modifier et le redistribuer, à condition que toute version redistribuée,
modifiée ou non, reste sous la même licence et que son code source soit fourni.
Il est fourni sans aucune garantie.
