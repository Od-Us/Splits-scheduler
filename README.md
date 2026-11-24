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

Sur la carte de l'intégration, cliquer sur **Configurer**. Le menu propose, dans
cet ordre : *Réglages généraux*, *Pompes à chaleur*, *Groupes de splits*,
*Types de planning*, *Profils*, *Programme hebdomadaire*, *Enregistrer et fermer*.

- **Pompes à chaleur** : voir [Pompes à chaleur](#pompes-à-chaleur) ci-dessous.
- **Groupes de splits** : nom et thermostats du groupe. Les splits d'un groupe
  suivent le même programme ; ils peuvent dépendre de pompes à chaleur
  différentes.
  - **Décalage des consignes des splits** (dans le menu des groupes) : pour
    chaque split, un *décalage chauffage* et un *décalage froid* (de −3 à
    +3 °C, par pas de 0,5) ajoutés à la consigne **envoyée** au split, pour
    corriger son thermostat interne. Exemple : un split qui arrête de chauffer
    trop tôt (pièce à 19 °C pour 20 °C demandés) → décalage chauffage +1 : il
    reçoit 21 °C. Le décalage froid vaut aussi en déshumidification ; rien n'est
    décalé en ventilation ni à l'arrêt. C'est **transparent** : la consigne
    affichée (carte, courbes, capteur « Consigne », écarts des dérogations)
    reste celle du programme, et un split qui confirme la consigne décalée n'est
    pas en dérogation ; un réglage à la télécommande est lu décalage retiré. Un
    décalage modifié est appliqué dès l'enregistrement. Le décalage suit le
    split, même déplacé dans un autre groupe.
- **Unité extérieure silencieuse** 🤫 (dans chaque profil) : *Activée*,
  *Désactivée* ou vide (ne pas modifier). Réglée par l'interrupteur « Quiet
  outdoor » que Faikout publie dans Home Assistant (option **« HA switches »**
  du module) ; proposée seulement si au moins un split a cet interrupteur, et
  ignorée par un split qui ne l'a pas (message dans le journal). Elle agit sur
  l'unité extérieure : si plusieurs splits la partagent, elle vaut pour tous.
  **Ce n'est jamais une dérogation** : la changer à la télécommande ou depuis
  la carte ne suspend pas la programmation ; le profil suivant qui précise ce
  réglage le réapplique. Attribut `silence_exterieur` du sélecteur de profil :
  interrupteur trouvé et état, pour chaque split. Le préréglage du split
  (Normal / ECONO / Powerful) n'est pas géré par l'intégration, sauf option
  ci-dessous.
- **Réglages généraux, multi-split** (deux options cumulables, désactivées par
  défaut) : *Envoyer le préréglage Normal à chaque commande* (coupe ECONO et
  Powerful) et *Envoyer « unité extérieure silencieuse » activée à chaque
  commande* (prime sur le réglage des profils). « Chaque commande » : tout envoi
  à un split — application d'un profil, réglage manuel depuis la carte,
  consigne adaptée à l'extérieur ; les deux sont renvoyés même si le split les
  indique déjà. Un bouton de la carte qui coupe le silence reste possible,
  mais la commande suivante le réactive.
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
    **supprimer**, ou **ajouter** une ligne.
  - **Avertissement pompe à chaleur** : si un split du groupe partage sa pompe
    à chaleur avec un split prioritaire d'un autre groupe, la semaine affiche
    les plages où les deux programmes s'opposent (« Lun 14:00–16:00 :
    chauffage ici, froid pour Séjour… ») : ces splits resteraient en veille. Les lignes sont toujours triées par
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
  **+30min** du bandeau règlent une **durée à partir de maintenant** : un appui
  sur +30 prévoit le retour à la programmation dans 30 minutes, puis 1 h,
  1 h 30… (au plus 24 h) ; −30 la réduit, et revenir à zéro rend « jusqu'au
  prochain créneau ». Le bandeau affiche la durée à gauche des boutons
  (« Durée : 1h30 », temps restant, ou « Durée : aucune ») et, en dessous,
  « Jusqu'au prochain créneau (17:00) » ou « Reprise 11:05 · 10:30 Eco ignoré ·
  ensuite Eco ». La durée choisie l'emporte : un créneau passé pendant la dérogation est ignoré, et à l'heure de
  reprise le profil prévu à ce moment est appliqué. L'heure de reprise survit à
  un redémarrage ; attributs `reprise`, `reprise_profil`, `creneau_ignore`,
  `derogation_depuis` sur le sélecteur de profil.
- **Ventilateur et oscillation** : les changer (télécommande, carte,
  thermostat) **n'est pas une dérogation** ; la programmation continue, et le
  prochain changement de profil rétablit les valeurs prévues.
- **Réglage sur un split** (télécommande, fenêtre de son thermostat) : si un
  split s'écarte du profil appliqué (mode, consigne à plus de 0,3 °C près)
  plus de 2 minutes après l'envoi, **ce split
  seul** passe en dérogation (pour un groupe d'un seul split, c'est **tout le
  groupe**, dont la consigne suit alors celle du split) ; les autres splits du groupe
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
    réglages manuels proposés (consigne, mode, ventilateur — listes
    déroulantes —, oscillation, **unité extérieure silencieuse**). Ce dernier
    est un interrupteur, affiché seulement si un split du groupe a
    l'interrupteur Faikout ; un appui ne vaut pas dérogation, affiche aussitôt
    le nouvel état puis celui des splits, et signale un split qui ne répond pas ;
  - **compresseur** : fréquence et charge (une pastille par pompe à chaleur
    si les splits du groupe en utilisent plusieurs : « PAC A 42 Hz · 52 % »),
    démarrages par heure ;
  - **frise du compresseur** (facultative) : sous la frise des profils, une
    bande fine montre les périodes de marche du compresseur aujourd'hui,
    **colorées selon sa vitesse** (du blanc, vitesse faible, au bleu foncé),
    et un trait à chaque démarrage, avec leur nombre en légende ;
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

**Panneaux des pompes à chaleur** (option de la carte : *Aucun*, *Pompes des
groupes affichés* ou *Toutes les pompes*) : un panneau repliable par pompe, avec
son mode (chauffage, froid, conflit, arrêt), une jauge de charge, la fréquence
du compresseur, la puissance, la consommation du jour, la température
extérieure (capteur Faikout d'un de ses splits), le split prioritaire (★) et le
mode de chaque split (un clic ouvre son thermostat).
Chaque panneau peut afficher en plus **un ou plusieurs capteurs au choix**
(n'importe quelle entité : bruit, débit, température de l'unité…), avec un
**libellé** au choix (vide = nom du capteur), réglés dans l'éditeur de la carte
sous *Capteurs supplémentaires des pompes à chaleur* ; un clic sur la valeur
ouvre l'entité.

Un clic sur le **nom du groupe** affiche ses splits (mode, consigne, température
mesurée, ou « injoignable ») ; un clic sur un split ouvre la fenêtre de son
thermostat.

Un clic sur les **frises ou les courbes** ouvre une **vue détaillée** : jour,
3 jours ou semaine, flèches pour remonter dans le temps, frise des profils
réellement appliqués (dérogations comprises), marches du compresseur et nombre
de démarrages, courbes ambiance / consigne / extérieur à afficher ou masquer,
charge du compresseur (simple ligne ; comme la frise, elle suit la **médiane** des capteurs du compresseur de la pompe principale), et une bande par **capteur
supplémentaire** du groupe (humidité, CO₂…) avec sa propre échelle et son unité,
curseur donnant toutes les valeurs à l'instant choisi. Par défaut, seules les **températures** sont
affichées (consigne, ambiance, extérieur, dérogations, et les capteurs
supplémentaires en °C) ; la charge du compresseur et les autres capteurs
s'activent d'un clic. Le bouton **Lissage 5 min** trace les courbes mesurées
(ambiance, extérieur, capteurs supplémentaires) en **moyenne glissante sur 5
minutes**, pour gommer les dents de scie des thermomètres ; les consignes
restent en escalier. L'option de la carte *Lisser les courbes* l'active par
défaut, et l'applique aussi aux courbes du jour de la carte. Plein écran sur
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

## Pompes à chaleur

Une pompe à chaleur (unité extérieure) alimente plusieurs splits par **un même
compresseur**. Menu **Pompes à chaleur** : ajouter, modifier, supprimer.

| Champ | Rôle |
|---|---|
| Nom, modèle | affichés sur la carte et dans l'appareil créé |
| Splits reliés | un split n'appartient qu'à une seule pompe |
| Split prioritaire (facultatif) | réglage « pièce prioritaire » de l'unité extérieure : son mode chaud/froid s'impose |
| Capteurs du compresseur (facultatif) | vide : capteurs « Compressor » de Faikout détectés sur les splits ; leur **médiane** est retenue |
| Fréquence maximale (facultatif) | voir *Charge du compresseur* |
| Puissance (W), compteur d'énergie (kWh) (facultatifs) | consommation du jour |

**Conflits de mode** : une unité extérieure ne peut pas chauffer et refroidir
en même temps. Un split en chauffage alors que le split prioritaire est en froid
ou en déshumidification (ou l'inverse) reste en veille : la carte affiche une
alerte sur le groupe et sur le split. Ventilation, arrêt et automatique ne
comptent pas. Sans split prioritaire, ou s'il est en ventilation ou à l'arrêt,
tous les splits en chauffage et en froid sont signalés dès que les deux modes
coexistent. Attribut `conflits_mode` du sélecteur de profil de chaque groupe.

**Consommation du jour** : avec un compteur d'énergie, différence depuis minuit
(une remise à zéro du compteur est gérée) ; sinon intégration de la puissance
minute par minute. Remise à zéro à minuit.

Entités de chaque pompe (appareil « <nom de la pompe> ») :

| Entité | Valeur |
|---|---|
| `sensor.<pompe>_mode` | `heat`, `cool`, `conflict` ou `idle` ; attributs `splits` (mode de chaque split), `split_prioritaire`, `conflits` |
| `sensor.<pompe>_compresseur` | fréquence (médiane des capteurs) |
| `sensor.<pompe>_charge_du_compresseur` | charge en % |
| `sensor.<pompe>_consommation_du_jour` | kWh depuis minuit (si puissance ou compteur) |

**Mise à jour** : le capteur de compresseur et la fréquence maximale réglés
auparavant dans les groupes sont repris une fois dans une pompe « Pompe à
chaleur » regroupant les splits de ces groupes. Si vous avez plusieurs unités
extérieures, répartissez ensuite les splits en plusieurs pompes.

## Démarrages du compresseur

Les démarrages sont comptés pour chaque groupe sur sa **pompe principale** (celle
de la majorité de ses splits), à partir de la fréquence médiane de son
compresseur. Un démarrage est compté à chaque passage de 0 à une valeur
positive ; les valeurs indisponibles sont ignorées.

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

### Charge du compresseur (%)

Dans la configuration d'une pompe à chaleur, **Fréquence maximale du compresseur**
(facultatif) se saisit **dans l'unité du capteur** : Hz ou tours/min selon le
réglage de Faikout (`ha.comprpm`), d'après le manuel de service de l'unité
extérieure. Laissée vide, elle est **observée** : à partir des maxima horaires des
30 derniers jours (statistiques de l'enregistreur, sinon historique détaillé),
les valeurs nulles ou impossibles (plus de 250 Hz ou 15 000 tr/min) sont
écartées, puis la **3e plus forte heure** est retenue, pour qu'un pic isolé ne
fausse pas la référence. Recalculée toutes les 6 heures ; inconnue tant qu'il
n'y a pas 3 heures de marche.

Le capteur `sensor.<pompe>_charge_du_compresseur` (et, pour la pompe principale
de chaque groupe, `sensor.<groupe>_charge_du_compresseur`) donne la fréquence actuelle en
% de ce maximum (borné à 100 %), avec les attributs `frequence`,
`frequence_max`, `source_max` (`saisie` ou `observee_30j`) et `unite`.

Sur la carte, l'option **Fréquence actuelle et charge** affiche « Compresseur
26 Hz · 35 % ». La frise du
compresseur est colorée selon la vitesse, et la vue détaillée ajoute sous les
courbes une ligne **Charge du compresseur** (0 à 100 %), masquable, et la charge
dans l'infobulle.

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
