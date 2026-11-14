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
- Un **réglage manuel** est respecté jusqu'au prochain créneau programmé :
  fait sur un split (télécommande, fenêtre de son thermostat), il ne concerne
  que ce split ; fait depuis la carte (choix d'un profil, réglage manuel), il
  vaut pour tout le groupe.

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
- **Préréglage du split** (dans chaque profil) : *Ne pas modifier*, *Normal*,
  *ECONO* ou *Powerful*, selon ce qu'annoncent les splits (préréglages `home`,
  `eco`, `boost` de Faikout). ECONO limite la consommation (et la puissance),
  Powerful pousse l'appareil au maximum ; les deux s'excluent et *Normal* les
  coupe. Un split sans la valeur l'ignore. Powerful s'arrêtant de lui-même au
  bout d'un moment, son arrêt n'est pas pris pour une dérogation.
- **Fonctions Daikin** (dans chaque profil) : *Flux d'air confort* 🧸,
  *Purification Streamer* 🦠, *Capteur de présence* 🙆, *Unité extérieure
  silencieuse* 🤫 — *Activé*, *Désactivé* ou vide (ne pas modifier). Elles sont
  réglées par les interrupteurs que Faikout publie dans Home Assistant (option
  **« HA switches »** à activer dans Faikout) ; seules celles qu'au moins un split
  possède sont proposées, et un split qui n'a pas la fonction l'ignore (message
  dans le journal). Le flux confort coupe l'oscillation verticale : un profil
  qui demande les deux est refusé. Le capteur de présence n'est pas lisible
  dans Home Assistant (Faikout ne remonte que l'activation du mode, pas la
  détection) ; si le split change sa consigne à cause de lui, c'est une
  dérogation.
- **Profils de fonctionnement** : un champ laissé vide n'est *pas modifié* sur
  les splits. Par exemple, un profil qui ne fixe que la consigne garde le mode
  en cours. Les vitesses de ventilateur et les oscillations proposées sont
  celles que vos splits annoncent (`fan_modes`, `swing_modes`…) ; on peut aussi
  saisir une valeur.
- **Types de planning** : ajout (éventuellement en copiant les programmes d'un
  planning existant), modification, suppression. Chaque planning a sa liste de
  **profils autorisés** (par exemple, pas de climatisation dans un planning
  d'hiver) : seuls ces profils sont proposés dans son programme, sur la carte et
  dans le sélecteur de profil des groupes qui le suivent (un autre profil est
  refusé). Un profil utilisé dans le programme ne peut pas être décoché. Les
  plannings existants autorisent tous les profils ; un nouveau profil est
  autorisé partout, à décocher si besoin.
- **Programme hebdomadaire d'un groupe** : choisir un planning et un groupe.
  La semaine s'affiche jour par jour avec le résumé des changements ; un jour
  vide indique le profil hérité (« Aucun changement — Eco depuis samedi 23:00 »).
  - Dans un jour : choisir une ligne pour la **modifier** (heure, profil) ou la
    **supprimer**, ou **ajouter** une ligne. Les lignes sont toujours triées par
    heure : une ligne ajoutée à 12:00 s'insère d'elle-même entre 08:30 et 17:00.
    Chaque profil proposé affiche ses réglages (« Confort — Chauffage · 20 °C »).
  - *Copier ce jour vers d'autres jours*, *Vider la journée*.
  - *Copier ce programme vers d'autres groupes ou plannings* : toute la
    semaine du groupe remplace celle des groupes cochés, dans les plannings
    cochés (par défaut le planning en cours d'édition). Refusé si un profil du
    programme n'est pas autorisé dans un planning de destination.
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
| `sensor.<groupe>_consigne` | Consigne du groupe (°C) : profil, adaptation à l'extérieur ou réglage depuis la carte ; vide si la programmation est coupée ou le profil en arrêt. Enregistrée pour les courbes (avant son apparition, les courbes reprennent la consigne du premier split). |
| `sensor.<groupe>_statut` | `Programmé`, `Dérogation`, `Programmation désactivée` ou `Aucun programme`. |
| `sensor.<groupe>_prochain_changement` | Date du prochain changement ; attribut `prochain_profil`. |

Et une entité globale : `select.programmation_des_splits_planning_de_tous_les_groupes`.
Elle affiche le planning commun à tous les groupes, ou *inconnu* s'ils diffèrent.

Les identifiants exacts dépendent de la langue de Home Assistant lors de la
création des entités ; ils se retrouvent dans la page de l'appareil.

## Comportement en détail

- **Durée d'une dérogation** : par défaut (et pour un changement fait à la
  télécommande), jusqu'au prochain créneau. Sur la carte, les boutons **−30min** et
  **+30min** du bandeau de dérogation avancent ou reculent l'heure de reprise
  (entre 30 minutes et 24 heures à partir de maintenant). La durée choisie
  l'emporte : un créneau passé pendant la dérogation est ignoré, et à l'heure de
  reprise le profil prévu à ce moment est appliqué. L'heure de reprise survit à
  un redémarrage ; attributs `reprise`, `reprise_profil`, `creneau_ignore`,
  `derogation_depuis` sur le sélecteur de profil.
- **Réglage sur un split** (télécommande, fenêtre de son thermostat) : si un
  split s'écarte du profil appliqué (mode, consigne à plus de 0,3 °C près,
  ventilateur, oscillation, préréglage, fonctions Daikin) plus de 2 minutes
  après l'envoi, **ce split seul** passe en dérogation (pour un groupe d'un seul
  split, c'est **tout le groupe**, dont la consigne suit alors celle du split) ; les autres splits du groupe
  continuent de suivre les créneaux et l'adaptation à l'extérieur. Il reprend
  au prochain créneau, ou à l'heure choisie avec ses boutons −30min / +30min,
  ou avec son bouton de reprise (bandeau ou liste des splits). Attribut
  `derogations_splits` du sélecteur de profil : split, début, reprise et écarts
  (`[{reglage, valeur, prevu}]`).
- **Réglage depuis la carte** (réglage manuel, choix d'un profil) : envoyé à
  tous les splits, **tout le groupe** passe en *Dérogation* (les dérogations
  des splits sont annulées). Rien n'est réimposé avant le prochain créneau,
  ou avant un appui sur *Reprendre la programmation*.
- **Changement de planning** (groupe ou tous les groupes) : la carte demande
  confirmation, car tous les splits concernés reçoivent aussitôt le nouveau
  profil ; les dérogations en cours sont annulées.
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
  - **thermomètre de chaque split** : un capteur de la pièce, qui remplace la
    température mesurée par le split (souvent faussée) ; vide = celle du split.
    L'ambiance affichée est la **moyenne des splits qui suivent le programme** ;
    un split en dérogation a sa propre pastille. Une carte réglée avec l'ancien
    champ unique « température ambiante » garde ce capteur pour tous les splits
    du groupe, jusqu'au choix d'un thermomètre par split ;
  - **capteurs supplémentaires** affichés sous l'état (humidité, CO₂…), avec
    un **libellé** au choix pour chacun (vide = nom du capteur) ;
  - **partie « Modifier »** : choix du planning du groupe, choix d'un profil,
    réglages manuels proposés (consigne, mode, ventilateur, préréglage —
    listes déroulantes —, oscillation) ; **Fonctions Daikin** (flux confort,
    Streamer, présence, extérieur silencieux, Powerful) en interrupteurs,
    affichés seulement pour les groupes dont un split possède la fonction ;
    les fonctions actives apparaissent aussi en pastilles sous la consigne et
    en icônes dans la liste des splits ;
    option **« boutons des fonctions Daikin »** pour les masquer. Un appui
    affiche tout de suite le nouvel état (« en attente du split… ») ; sans
    réponse du split, un message nomme l'interrupteur Faikout en cause. Les
    interrupteurs trouvés et leur état sont visibles dans l'attribut
    `fonctions_daikin` du sélecteur de profil du groupe ;
  - **frise du compresseur** (facultative) : sous la frise des profils, une
    bande fine montre les périodes de marche du compresseur aujourd'hui et un
    trait à chaque démarrage, avec leur nombre en légende ;
  - **courbes du jour** (facultatives) : consigne, ambiance et/ou température
    extérieure, de 0 h à 24 h sur le même axe que les frises (120 px de haut
    pour un groupe de plusieurs splits, 60 px sinon). En **trait plein** : la
    **consigne du groupe** (celle que la programmation impose, même si le
    premier split est en dérogation) et l'**ambiance moyenne** des splits qui
    suivent le programme. En **pointillés**, avec le nom du split en bout de
    trait : la consigne et l'ambiance d'un split **en dérogation**, c'est-à-dire
    dont la consigne (ou l'arrêt) s'écarte de celle du groupe à cet instant.
    La vue détaillée trace les mêmes courbes (bouton *Dérogations* pour masquer
    les pointillés) et donne au curseur les valeurs de chaque split en
    dérogation.

Un clic sur le **nom du groupe** affiche ses splits (mode, consigne, température
mesurée, ou « injoignable ») ; un clic sur un split ouvre la fenêtre de son
thermostat.

Un clic sur les **frises ou les courbes** ouvre une **vue détaillée** : jour,
3 jours ou semaine, flèches pour remonter dans le temps, frise des profils
réellement appliqués (dérogations comprises), marches du compresseur et nombre
de démarrages, courbes ambiance / consigne / extérieur à afficher ou masquer,
curseur donnant toutes les valeurs à l'instant choisi. Plein écran sur
téléphone. La navigation est limitée à l'historique détaillé de Home Assistant
(10 jours par défaut, réglage `purge_keep_days` de l'enregistreur).

Chaque groupe montre en permanence la **consigne** (en grand), le profil actif,
la température ambiante, le statut, la frise du jour et le prochain changement.
En dérogation, un bandeau indique l'heure de reprise et propose *Reprendre*.
Quand un seul split déroge, le statut le nomme (« Dérogation · Chambre 2 »),
son écart s'affiche sous la consigne (« Chambre 2 : 23,0 °C ») et il a son
propre bandeau ; la grande consigne reste celle des splits qui suivent le
programme. Si ces splits ne sont pas d'accord entre eux (par exemple un split
injoignable au moment de l'envoi), la carte affiche « Consignes différentes :
20 à 21,5 °C » ou « Modes différents ».
Le bouton **Modifier** déplie le planning, les profils, les réglages manuels et
l'interrupteur de programmation. Un réglage manuel est envoyé à **tous les
splits du groupe** et vaut dérogation jusqu'au prochain créneau.

Après une mise à jour, si le navigateur ou l'application affiche encore
l'ancienne carte (cache), un bandeau le signale avec un bouton *Recharger*.

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
    thermometers:                 # thermomètre de chaque split (facultatif)
      climate.salon: sensor.salon_temperature
    sensors: [sensor.salon_humidite]
    sensor_names: {sensor.salon_humidite: Humidité}   # facultatif
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
- après un réglage manuel depuis la carte, plus d'adaptation jusqu'au
  prochain créneau ; un split en dérogation n'est pas adapté, les autres le
  restent.

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
