#!/usr/bin/env python3
# Generates README.md (English) and README.<lang>.md at the repo root
# from the translations below. Each file shows the 8 *other* languages as a flag row.
# Same architecture as the alfred-path sibling project.
import os
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(OUT, exist_ok=True)

LANGS = [("en","🇬🇧","English"),("fr","🇫🇷","Français"),("de","🇩🇪","Deutsch"),
         ("es","🇪🇸","Español"),("it","🇮🇹","Italiano"),("pt","🇵🇹","Português"),
         ("ja","🇯🇵","日本語"),("zh","🇨🇳","中文"),("el","🇬🇷","Ελληνικά")]
def fname(code):
    return "README.md" if code == "en" else f"README.{code}.md"

def nav(current):
    cells = "".join(
        f'<td align="center"><a href="{fname(c)}"><img src="assets/flags/{c}.png" width="40" alt="{n}"></a><br>'
        f'<a href="{fname(c)}"><sub>{n}</sub></a></td>'
        for c, _, n in LANGS if c != current)
    return f"<table>\n  <tr>{cells}</tr>\n</table>"

TEMPLATE = """<a href="dist/The-Noun-Project.alfredworkflow?raw=true"><img src="assets/download/{code}.png" width="240" align="right" alt="{btn_alt}"></a>

{nav}

###### ALFRED WORKFLOW
# {title}

**{pitch}**

{tagline}

<img src="screenshots/usage.png" width="640" alt="{alt_usage}">

## ✨ {h_what}

- **{f1_t}** → {f1_d}
- **{f2_t}** → {f2_d}
- **{f3_t}** → {f3_d}
- **{f4_t}** → {f4_d}
- **{f5_t}** → {f5_d}
- **{f6_t}** → {f6_d}
- **{f7_t}** → {f7_d}

## 🚀 {h_install}

1. {inst1}
2. {inst2}
3. {inst3}
4. {inst4}

{requires}

## ⚙️ {h_config}

<img src="screenshots/settings.png" width="640" alt="{alt_settings}">

{config_p}

## ⌨️ {h_keys}

| {key_col} | {action_col} |
|---|---|
| ⏎ | {k_enter} |
| ⌥⏎ | {k_alt} |
| ⌃⏎ | {k_ctrl} |
| ⇧⏎ | {k_shift} |
| ⇧⌥⏎ | {k_shift_alt} |
| ⇧⌃⏎ | {k_shift_ctrl} |
| ⌘⏎ | {k_cmd} |
| ⌘⌥⏎ | {k_cmd_alt} |
| ⌘⇧⏎ | {k_cmd_shift} |
| ⌘⇧⌥⏎ | {k_cmd_shift_alt} |
| ⌘⌥⌃⏎ | {k_cmd_alt_ctrl} |
| ⌘⌥⇧⌃⏎ | {k_all} |
| ⇥ | {k_tab} |
| ⌘Y | {k_ql} |

{ctl_p}

## 🔧 {h_how}

{how_p1}

{how_p2}

## 🛠 {h_dev}

```bash
(cd workflow && zip -r "../dist/The-Noun-Project.alfredworkflow" . -x '.*' -x '__pycache__/*')  # {c_zip}
osascript -l JavaScript tools/make-icon.js "$PWD/workflow/icon.png"  # {c_icon}
node tools/make-screenshots.mjs   # {c_shots}
tools/make-readmes.py             # {c_readmes}
tools/make-buttons.py             # {c_buttons}
```

- {dev1}
- {dev2}
- {dev3}

## 📚 {h_refs}

- [Alfred](https://www.alfredapp.com) · [Powerpack](https://www.alfredapp.com/powerpack/) · [{ref_docs}](https://www.alfredapp.com/help/workflows/)
- [The Noun Project](https://thenounproject.com) · [{ref_api}](https://api.thenounproject.com) · [{ref_terms}](https://thenounproject.com/legal/terms-of-use/)
- [Playwright](https://playwright.dev)

## 📄 {h_license}

{license_p}

---

{footer}
"""

T = {}
T["en"] = dict(
 title="Search and download Noun Project icons",
 btn_alt="Download the workflow",
 pitch="Search millions of Noun Project icons and grab the SVG or PNG without leaving your keyboard.",
 tagline="Type `noun house`, pick, press **⏎**. The file lands in your folder — clean, at the right size.",
 alt_usage="Searching “noun maison” in Alfred", alt_settings="Workflow configuration",
 h_what="What it does",
 f1_t="Instant search", f1_d="results with thumbnails; public-domain icons come first, tagged 🟢",
 f2_t="A whole shortcut grid", f2_d="⏎ downloads the default format, ⌥ switches to the other one, ⇧ copies instead of saving, ⌃ targets the attribution (.txt), and ⌘ combines them — up to ⌘⌥⇧⌃⏎, which copies everything in a row",
 f3_t="Options flow", f3_d="the ▸ submenu (⇥ autocomplete) lists all twelve actions plus a guided flow: format → size → destination folder",
 f4_t="Attribution at hand", f4_d="the credit line can be saved as .txt or copied, alone or along with the image (successive copies all land in your clipboard history)",
 f5_t="Cleanup", f5_d="the embedded “Created by…” notice in free files is removed (PNG cropped, text stripped from the SVG code); CC BY then requires credit elsewhere — ⇧⌃⏎ copies it",
 f6_t="Your own session", f6_d="an invisible background Chrome uses your thenounproject.com account — full catalogue, according to your subscription",
 f7_t="Localized", f7_d="interface and notifications follow your macOS language (English, French, German, Spanish, Italian, Portuguese, Japanese, Chinese, Greek)",
 h_install="Install",
 inst1="Download `The-Noun-Project.alfredworkflow` and double-click it",
 inst2="Install Node.js if needed: `brew install node` (Python 3 comes with the Command Line Tools: `xcode-select --install`)",
 inst3="Run a first search — `noun house` — Playwright and Chromium install themselves (a few minutes, once)",
 inst4="Type `nounctl` → “Sign in”: a Chrome window opens, sign in on the site, it closes by itself. The session persists in a dedicated profile, separate from your everyday browser",
 requires="Requires [Alfred 5](https://www.alfredapp.com) with the [Powerpack](https://www.alfredapp.com/powerpack/).",
 h_config="Configuration",
 config_p="Backend (Browser or official API), default format (SVG or PNG — the other becomes the “alternate” one), keyword, download folder, default PNG size, colour, number of results, notice cleanup, reveal in Finder. In API mode (key/secret from [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/)), the free tier only allows public-domain downloads.",
 h_keys="Shortcuts", key_col="Key", action_col="Action",
 k_enter="Download the default format",
 k_alt="Download the alternate format",
 k_ctrl="Download the attribution as .txt",
 k_shift="Copy the default format to the clipboard",
 k_shift_alt="Copy the alternate format",
 k_shift_ctrl="Copy the attribution",
 k_cmd="Download attribution + default format",
 k_cmd_alt="Download attribution + alternate format",
 k_cmd_shift="Copy the attribution, then the default format",
 k_cmd_shift_alt="Copy the attribution, then the alternate format",
 k_cmd_alt_ctrl="Download both formats + the attribution",
 k_all="Copy the attribution, the alternate, then the default format",
 k_tab="Submenu with every action (autocomplete — if ⇥ isn't bound to Alfred's Universal Actions)",
 k_ql="Quick Look preview of the icon's page",
 ctl_p="`nounctl`: sign-in, status, stop/restart of the background browser, reinstall, logs.",
 h_how="How it works",
 how_p1="A Node/[Playwright](https://playwright.dev) daemon ([`workflow/server.mjs`](workflow/server.mjs)) runs in the background with an invisible Chromium and a persistent profile. Search goes through the site's internal API (no account needed); downloads go through the `downloadIcon` GraphQL mutation with your session — the file comes back as base64, gets cleaned up, then saved or copied. The daemon stops after 3 hours of inactivity and restarts on demand.",
 how_p2="No credentials ever pass through the workflow: you sign in by hand in the Chrome window, and the cookies stay in the local profile. This automates your own session, for your personal use — stay within your subscription and the site's terms of use.",
 h_dev="Development",
 c_zip="package the workflow", c_icon="regenerate workflow/icon.png", c_shots="regenerate the screenshots", c_readmes="regenerate all README files", c_buttons="regenerate the download buttons",
 dev1="`workflow/` — sources: `info.plist`, Python scripts (stdlib only), the `server.mjs` daemon, `i18n.py` (9 languages)",
 dev2="The daemon exposes a small local HTTP API (`/search`, `/download`, `/login`, `/status`, `/quit`) on 127.0.0.1",
 dev3="`dist/` — the installable bundle",
 h_refs="References", ref_docs="Workflows documentation", ref_api="Official API", ref_terms="Licenses",
 h_license="License",
 license_p="MIT. The icons themselves remain governed by The Noun Project licenses (CC BY or public domain, subscription where applicable).",
 footer="Made by <a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · Issues and PRs welcome",
)

T["fr"] = dict(
 title="Chercher et télécharger des icônes Noun Project",
 btn_alt="Télécharger le workflow",
 pitch="Cherchez parmi des millions de pictogrammes Noun Project et récupérez le SVG ou le PNG sans quitter le clavier.",
 tagline="Tapez `noun maison`, choisissez, pressez **⏎**. Le fichier arrive dans votre dossier — propre, à la bonne taille.",
 alt_usage="Recherche « noun maison » dans Alfred", alt_settings="Configuration du workflow",
 h_what="Ce que ça fait",
 f1_t="Recherche instantanée", f1_d="résultats avec vignettes ; les icônes du domaine public arrivent en premier, étiquetées 🟢",
 f2_t="Toute une grille de raccourcis", f2_d="⏎ télécharge le format par défaut, ⌥ bascule sur l'autre, ⇧ copie au lieu d'enregistrer, ⌃ vise l'attribution (.txt), et ⌘ combine — jusqu'à ⌘⌥⇧⌃⏎ qui copie tout à la suite",
 f3_t="Flux d'options", f3_d="le sous-menu ▸ (autocomplétion ⇥) liste les douze actions plus un flux guidé : format → taille → dossier de destination",
 f4_t="Attribution à portée de main", f4_d="la mention de crédit s'enregistre en .txt ou se copie, seule ou avec l'image (les copies successives restent dans l'historique du presse-papiers)",
 f5_t="Nettoyage", f5_d="la mention « Created by… » incrustée dans les fichiers gratuits est retirée (PNG rogné, texte supprimé du code SVG) ; la licence CC BY exige alors un crédit ailleurs — ⇧⌃⏎ le copie",
 f6_t="Votre propre session", f6_d="un Chrome invisible en arrière-plan utilise votre compte thenounproject.com — catalogue complet, selon votre abonnement",
 f7_t="Localisé", f7_d="interface et notifications suivent la langue de votre macOS (anglais, français, allemand, espagnol, italien, portugais, japonais, chinois, grec)",
 h_install="Installation",
 inst1="Téléchargez `The-Noun-Project.alfredworkflow` et double-cliquez dessus",
 inst2="Installez Node.js si nécessaire : `brew install node` (Python 3 vient des Command Line Tools : `xcode-select --install`)",
 inst3="Lancez une première recherche — `noun maison` — Playwright et Chromium s'installent tout seuls (quelques minutes, une seule fois)",
 inst4="Tapez `nounctl` → « Se connecter » : une fenêtre Chrome s'ouvre, identifiez-vous sur le site, elle se referme seule. La session persiste dans un profil dédié, séparé de votre navigateur habituel",
 requires="Nécessite [Alfred 5](https://www.alfredapp.com) avec le [Powerpack](https://www.alfredapp.com/powerpack/).",
 h_config="Configuration",
 config_p="Backend (Navigateur ou API officielle), format par défaut (SVG ou PNG — l'autre devient l'« alternatif »), mot-clé, dossier de téléchargement, taille PNG par défaut, couleur, nombre de résultats, nettoyage de la mention, révélation dans le Finder. En mode API (clé/secret sur [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/)), l'accès gratuit limite les téléchargements au domaine public.",
 h_keys="Raccourcis", key_col="Touche", action_col="Action",
 k_enter="Télécharger le format par défaut",
 k_alt="Télécharger le format alternatif",
 k_ctrl="Télécharger l'attribution en .txt",
 k_shift="Copier le format par défaut dans le presse-papiers",
 k_shift_alt="Copier le format alternatif",
 k_shift_ctrl="Copier l'attribution",
 k_cmd="Télécharger l'attribution + le format par défaut",
 k_cmd_alt="Télécharger l'attribution + le format alternatif",
 k_cmd_shift="Copier l'attribution, puis le format par défaut",
 k_cmd_shift_alt="Copier l'attribution, puis le format alternatif",
 k_cmd_alt_ctrl="Télécharger les deux formats + l'attribution",
 k_all="Copier l'attribution, l'alternatif, puis le format par défaut",
 k_tab="Sous-menu de toutes les actions (autocomplétion — si ⇥ n'est pas assignée aux Universal Actions d'Alfred)",
 k_ql="Aperçu Quick Look de la page de l'icône",
 ctl_p="`nounctl` : connexion, état, arrêt/redémarrage du navigateur de fond, réinstallation, journaux.",
 h_how="Comment ça marche",
 how_p1="Un démon Node/[Playwright](https://playwright.dev) ([`workflow/server.mjs`](workflow/server.mjs)) tourne en arrière-plan avec un Chromium invisible et un profil persistant. La recherche interroge l'API interne du site (sans compte) ; le téléchargement passe par la mutation GraphQL `downloadIcon` avec votre session — le fichier arrive en base64, est nettoyé, puis enregistré ou copié. Le démon s'arrête après 3 h d'inactivité et redémarre à la demande.",
 how_p2="Aucun identifiant ne transite par le workflow : la connexion se fait à la main dans la fenêtre Chrome, les cookies restent dans le profil local. Ce mode automatise votre propre session, pour votre usage personnel — restez dans les limites de votre abonnement et des CGU du site.",
 h_dev="Développement",
 c_zip="empaquette le workflow", c_icon="régénère workflow/icon.png", c_shots="régénère les captures", c_readmes="régénère tous les README", c_buttons="régénère les boutons de téléchargement",
 dev1="`workflow/` — sources : `info.plist`, scripts Python (stdlib uniquement), le démon `server.mjs`, `i18n.py` (9 langues)",
 dev2="Le démon expose une petite API HTTP locale (`/search`, `/download`, `/login`, `/status`, `/quit`) sur 127.0.0.1",
 dev3="`dist/` — le paquet installable",
 h_refs="Références", ref_docs="Documentation des workflows", ref_api="API officielle", ref_terms="Licences",
 h_license="Licence",
 license_p="MIT. Les icônes restent soumises aux licences The Noun Project (CC BY ou domaine public, abonnement le cas échéant).",
 footer="Réalisé par <a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · Issues et PRs bienvenues",
)
T["de"] = dict(
 title="Noun-Project-Icons suchen und herunterladen",
 btn_alt="Workflow herunterladen",
 pitch="Durchsuche Millionen von Noun-Project-Icons und hole dir das SVG oder PNG, ohne die Tastatur zu verlassen.",
 tagline="`noun haus` tippen, auswählen, **⏎** drücken. Die Datei liegt in deinem Ordner – sauber und in der richtigen Größe.",
 alt_usage="Suche „noun maison“ in Alfred", alt_settings="Workflow-Konfiguration",
 h_what="Was es tut",
 f1_t="Sofortsuche", f1_d="Ergebnisse mit Vorschaubildern; gemeinfreie Icons erscheinen zuerst, markiert mit 🟢",
 f2_t="Ein ganzes Raster an Tastenkürzeln", f2_d="⏎ lädt das Standardformat herunter, ⌥ wechselt zum anderen, ⇧ kopiert statt zu speichern, ⌃ zielt auf den Attributionshinweis (.txt), und ⌘ kombiniert – bis hin zu ⌘⌥⇧⌃⏎, das alles nacheinander kopiert",
 f3_t="Optionsablauf", f3_d="das Untermenü ▸ (Autovervollständigung mit ⇥) listet alle zwölf Aktionen plus einen geführten Ablauf: Format → Größe → Zielordner",
 f4_t="Attribution griffbereit", f4_d="der Attributionshinweis lässt sich als .txt speichern oder kopieren, allein oder zusammen mit dem Bild (aufeinanderfolgende Kopien landen alle im Verlauf deiner Zwischenablage)",
 f5_t="Bereinigung", f5_d="der in Gratisdateien eingebettete Hinweis „Created by…“ wird entfernt (PNG beschnitten, Text aus dem SVG-Code gelöscht); die CC-BY-Lizenz verlangt dann eine Namensnennung an anderer Stelle – ⇧⌃⏎ kopiert sie",
 f6_t="Deine eigene Sitzung", f6_d="ein unsichtbares Chrome im Hintergrund nutzt dein Konto auf thenounproject.com – voller Katalog, je nach Abo",
 f7_t="Lokalisiert", f7_d="Oberfläche und Mitteilungen folgen deiner macOS-Sprache (Englisch, Französisch, Deutsch, Spanisch, Italienisch, Portugiesisch, Japanisch, Chinesisch, Griechisch)",
 h_install="Installation",
 inst1="`The-Noun-Project.alfredworkflow` herunterladen und doppelklicken",
 inst2="Bei Bedarf Node.js installieren: `brew install node` (Python 3 kommt mit den Command Line Tools: `xcode-select --install`)",
 inst3="Eine erste Suche starten – `noun haus` – Playwright und Chromium installieren sich von selbst (einige Minuten, nur einmal)",
 inst4="`nounctl` tippen → „Anmelden“: Ein Chrome-Fenster öffnet sich, dort auf der Website anmelden, es schließt sich von selbst. Die Sitzung bleibt in einem eigenen Profil erhalten, getrennt von deinem gewohnten Browser",
 requires="Benötigt [Alfred 5](https://www.alfredapp.com) mit [Powerpack](https://www.alfredapp.com/powerpack/).",
 h_config="Konfiguration",
 config_p="Backend (Browser oder offizielle API), Standardformat (SVG oder PNG – das andere wird zum „Alternativformat“), Schlüsselwort, Download-Ordner, PNG-Standardgröße, Farbe, Anzahl der Ergebnisse, Bereinigung des Hinweises, Anzeigen im Finder. Im API-Modus (Key/Secret auf [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/)) beschränkt der Gratiszugang die Downloads auf die Public Domain.",
 h_keys="Tastenkürzel", key_col="Taste", action_col="Aktion",
 k_enter="Standardformat herunterladen",
 k_alt="Alternativformat herunterladen",
 k_ctrl="Attributionshinweis als .txt herunterladen",
 k_shift="Standardformat in die Zwischenablage kopieren",
 k_shift_alt="Alternativformat kopieren",
 k_shift_ctrl="Attributionshinweis kopieren",
 k_cmd="Attributionshinweis + Standardformat herunterladen",
 k_cmd_alt="Attributionshinweis + Alternativformat herunterladen",
 k_cmd_shift="Attributionshinweis kopieren, dann das Standardformat",
 k_cmd_shift_alt="Attributionshinweis kopieren, dann das Alternativformat",
 k_cmd_alt_ctrl="Beide Formate + Attributionshinweis herunterladen",
 k_all="Attributionshinweis, dann das Alternativ-, dann das Standardformat kopieren",
 k_tab="Untermenü mit allen Aktionen (Autovervollständigung – falls ⇥ nicht mit Alfreds Universal Actions belegt ist)",
 k_ql="Quick-Look-Vorschau der Icon-Seite",
 ctl_p="`nounctl`: Anmeldung, Status, Stoppen/Neustarten des Hintergrund-Browsers, Neuinstallation, Logs.",
 h_how="So funktioniert es",
 how_p1="Ein Node/[Playwright](https://playwright.dev)-Daemon ([`workflow/server.mjs`](workflow/server.mjs)) läuft im Hintergrund mit einem unsichtbaren Chromium und einem persistenten Profil. Die Suche fragt die interne API der Website ab (ohne Konto); der Download läuft über die GraphQL-Mutation `downloadIcon` mit deiner Sitzung – die Datei kommt als Base64 an, wird bereinigt und dann gespeichert oder kopiert. Der Daemon beendet sich nach 3 Stunden Inaktivität und startet bei Bedarf neu.",
 how_p2="Keine Zugangsdaten laufen durch den Workflow: Die Anmeldung erfolgt von Hand im Chrome-Fenster, die Cookies bleiben im lokalen Profil. Das automatisiert deine eigene Sitzung, für deinen persönlichen Gebrauch – bleib innerhalb der Grenzen deines Abos und der Nutzungsbedingungen der Website.",
 h_dev="Entwicklung",
 c_zip="den Workflow verpacken", c_icon="workflow/icon.png neu erzeugen", c_shots="die Screenshots neu erzeugen", c_readmes="alle README-Dateien neu erzeugen", c_buttons="die Download-Buttons neu erzeugen",
 dev1="`workflow/` – Quellen: `info.plist`, Python-Skripte (nur Stdlib), der Daemon `server.mjs`, `i18n.py` (9 Sprachen)",
 dev2="Der Daemon stellt eine kleine lokale HTTP-API (`/search`, `/download`, `/login`, `/status`, `/quit`) auf 127.0.0.1 bereit",
 dev3="`dist/` – das installierbare Paket",
 h_refs="Referenzen", ref_docs="Workflow-Dokumentation", ref_api="Offizielle API", ref_terms="Lizenzen",
 h_license="Lizenz",
 license_p="MIT. Die Icons selbst unterliegen weiterhin den Lizenzen von The Noun Project (CC BY oder Public Domain, gegebenenfalls Abo).",
 footer="Erstellt von <a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · Issues und PRs willkommen",
)
T["es"] = dict(
 title="Buscar y descargar iconos de Noun Project",
 btn_alt="Descargar el workflow",
 pitch="Busca entre millones de pictogramas de Noun Project y llévate el SVG o el PNG sin soltar el teclado.",
 tagline="Escribe `noun casa`, elige, pulsa **⏎**. El archivo aparece en tu carpeta — limpio y al tamaño correcto.",
 alt_usage="Búsqueda de «noun maison» en Alfred", alt_settings="Configuración del workflow",
 h_what="Qué hace",
 f1_t="Búsqueda instantánea", f1_d="resultados con miniaturas; los iconos de dominio público van primero, etiquetados 🟢",
 f2_t="Toda una cuadrícula de atajos", f2_d="⏎ descarga el formato por defecto, ⌥ cambia al otro, ⇧ copia en lugar de guardar, ⌃ apunta a la atribución (.txt), y ⌘ combina — hasta ⌘⌥⇧⌃⏎, que lo copia todo seguido",
 f3_t="Flujo de opciones", f3_d="el submenú ▸ (autocompletado ⇥) lista las doce acciones más un flujo guiado: formato → tamaño → carpeta de destino",
 f4_t="Atribución al alcance de la mano", f4_d="la mención de crédito se puede guardar como .txt o copiar, sola o junto con la imagen (las copias sucesivas quedan todas en el historial del portapapeles)",
 f5_t="Limpieza", f5_d="la mención «Created by…» incrustada en los archivos gratuitos se elimina (PNG recortado, texto suprimido del código SVG); la licencia CC BY exige entonces un crédito en otro lugar — ⇧⌃⏎ lo copia",
 f6_t="Tu propia sesión", f6_d="un Chrome invisible en segundo plano usa tu cuenta de thenounproject.com — catálogo completo, según tu suscripción",
 f7_t="Localizado", f7_d="interfaz y notificaciones siguen el idioma de tu macOS (inglés, francés, alemán, español, italiano, portugués, japonés, chino, griego)",
 h_install="Instalación",
 inst1="Descarga `The-Noun-Project.alfredworkflow` y haz doble clic",
 inst2="Instala Node.js si hace falta: `brew install node` (Python 3 viene con las Command Line Tools: `xcode-select --install`)",
 inst3="Lanza una primera búsqueda — `noun casa` — Playwright y Chromium se instalan solos (unos minutos, una sola vez)",
 inst4="Escribe `nounctl` → «Iniciar sesión»: se abre una ventana de Chrome, identifícate en el sitio y se cierra sola. La sesión persiste en un perfil dedicado, separado de tu navegador habitual",
 requires="Requiere [Alfred 5](https://www.alfredapp.com) con el [Powerpack](https://www.alfredapp.com/powerpack/).",
 h_config="Configuración",
 config_p="Backend (Navegador o API oficial), formato por defecto (SVG o PNG — el otro pasa a ser el «alternativo»), palabra clave, carpeta de descarga, tamaño PNG por defecto, color, número de resultados, limpieza de la mención, mostrar en el Finder. En modo API (clave/secreto en [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/)), el acceso gratuito limita las descargas al dominio público.",
 h_keys="Atajos", key_col="Tecla", action_col="Acción",
 k_enter="Descargar el formato por defecto",
 k_alt="Descargar el formato alternativo",
 k_ctrl="Descargar la atribución en .txt",
 k_shift="Copiar el formato por defecto al portapapeles",
 k_shift_alt="Copiar el formato alternativo",
 k_shift_ctrl="Copiar la atribución",
 k_cmd="Descargar la atribución + el formato por defecto",
 k_cmd_alt="Descargar la atribución + el formato alternativo",
 k_cmd_shift="Copiar la atribución y luego el formato por defecto",
 k_cmd_shift_alt="Copiar la atribución y luego el formato alternativo",
 k_cmd_alt_ctrl="Descargar los dos formatos + la atribución",
 k_all="Copiar la atribución, el alternativo y luego el formato por defecto",
 k_tab="Submenú con todas las acciones (autocompletado — si ⇥ no está asignada a las Universal Actions de Alfred)",
 k_ql="Vista previa Quick Look de la página del icono",
 ctl_p="`nounctl`: iniciar sesión, estado, parar/reiniciar el navegador de fondo, reinstalación, registros.",
 h_how="Cómo funciona",
 how_p1="Un demonio Node/[Playwright](https://playwright.dev) ([`workflow/server.mjs`](workflow/server.mjs)) corre en segundo plano con un Chromium invisible y un perfil persistente. La búsqueda consulta la API interna del sitio (sin cuenta); la descarga pasa por la mutación GraphQL `downloadIcon` con tu sesión — el archivo llega en base64, se limpia y después se guarda o se copia. El demonio se detiene tras 3 h de inactividad y se reinicia bajo demanda.",
 how_p2="Ninguna credencial pasa por el workflow: la conexión se hace a mano en la ventana de Chrome y las cookies se quedan en el perfil local. Este modo automatiza tu propia sesión, para tu uso personal — mantente dentro de los límites de tu suscripción y de las condiciones de uso del sitio.",
 h_dev="Desarrollo",
 c_zip="empaqueta el workflow", c_icon="regenera workflow/icon.png", c_shots="regenera las capturas", c_readmes="regenera todos los README", c_buttons="regenera los botones de descarga",
 dev1="`workflow/` — fuentes: `info.plist`, scripts Python (solo stdlib), el demonio `server.mjs`, `i18n.py` (9 idiomas)",
 dev2="El demonio expone una pequeña API HTTP local (`/search`, `/download`, `/login`, `/status`, `/quit`) en 127.0.0.1",
 dev3="`dist/` — el paquete instalable",
 h_refs="Referencias", ref_docs="Documentación de workflows", ref_api="API oficial", ref_terms="Licencias",
 h_license="Licencia",
 license_p="MIT. Los iconos siguen sujetos a las licencias de The Noun Project (CC BY o dominio público, suscripción cuando corresponda).",
 footer="Hecho por <a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · Issues y PRs bienvenidos",
)
T["it"] = dict(
 title="Cerca e scarica icone Noun Project",
 btn_alt="Scarica il workflow",
 pitch="Cerca tra milioni di pittogrammi Noun Project e ottieni l'SVG o il PNG senza staccare le mani dalla tastiera.",
 tagline="Digita `noun casa`, scegli, premi **⏎**. Il file arriva nella tua cartella — pulito, alla dimensione giusta.",
 alt_usage="Ricerca «noun maison» in Alfred", alt_settings="Configurazione del workflow",
 h_what="Cosa fa",
 f1_t="Ricerca istantanea", f1_d="risultati con miniature; le icone di pubblico dominio arrivano per prime, contrassegnate 🟢",
 f2_t="Un'intera griglia di scorciatoie", f2_d="⏎ scarica il formato predefinito, ⌥ passa all'altro, ⇧ copia invece di salvare, ⌃ punta alla menzione di attribuzione (.txt), e ⌘ combina — fino a ⌘⌥⇧⌃⏎, che copia tutto in sequenza",
 f3_t="Flusso di opzioni", f3_d="il sottomenu ▸ (autocompletamento ⇥) elenca tutte e dodici le azioni più un flusso guidato: formato → dimensione → cartella di destinazione",
 f4_t="Attribuzione a portata di mano", f4_d="la menzione di attribuzione si salva in .txt o si copia, da sola o insieme all'immagine (le copie successive restano tutte nella cronologia degli appunti)",
 f5_t="Pulizia", f5_d="la dicitura «Created by…» incorporata nei file gratuiti viene rimossa (PNG ritagliato, testo eliminato dal codice SVG); la licenza CC BY richiede allora un credito altrove — ⇧⌃⏎ lo copia",
 f6_t="Sessione personale", f6_d="un Chrome invisibile in background usa il tuo account thenounproject.com — catalogo completo, in base al tuo abbonamento",
 f7_t="Localizzato", f7_d="interfaccia e notifiche seguono la lingua del tuo macOS (inglese, francese, tedesco, spagnolo, italiano, portoghese, giapponese, cinese, greco)",
 h_install="Installazione",
 inst1="Scarica `The-Noun-Project.alfredworkflow` e fai doppio clic",
 inst2="Installa Node.js se necessario: `brew install node` (Python 3 arriva con i Command Line Tools: `xcode-select --install`)",
 inst3="Lancia una prima ricerca — `noun casa` — Playwright e Chromium si installano da soli (qualche minuto, una sola volta)",
 inst4="Digita `nounctl` → «Accedi»: si apre una finestra Chrome, effettua l'accesso al sito e la finestra si chiude da sola. La sessione persiste in un profilo dedicato, separato dal tuo browser abituale",
 requires="Richiede [Alfred 5](https://www.alfredapp.com) con il [Powerpack](https://www.alfredapp.com/powerpack/).",
 h_config="Configurazione",
 config_p="Backend (Browser o API ufficiale), formato predefinito (SVG o PNG — l'altro diventa l'«alternativo»), parola chiave, cartella di download, dimensione PNG predefinita, colore, numero di risultati, pulizia della dicitura, visualizzazione nel Finder. In modalità API (chiave/segreto su [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/)), l'accesso gratuito limita i download al pubblico dominio.",
 h_keys="Scorciatoie", key_col="Tasto", action_col="Azione",
 k_enter="Scarica il formato predefinito",
 k_alt="Scarica il formato alternativo",
 k_ctrl="Scarica la menzione di attribuzione in .txt",
 k_shift="Copia il formato predefinito negli appunti",
 k_shift_alt="Copia il formato alternativo",
 k_shift_ctrl="Copia la menzione di attribuzione",
 k_cmd="Scarica l'attribuzione + il formato predefinito",
 k_cmd_alt="Scarica l'attribuzione + il formato alternativo",
 k_cmd_shift="Copia l'attribuzione, poi il formato predefinito",
 k_cmd_shift_alt="Copia l'attribuzione, poi il formato alternativo",
 k_cmd_alt_ctrl="Scarica entrambi i formati + l'attribuzione",
 k_all="Copia l'attribuzione, l'alternativo, poi il formato predefinito",
 k_tab="Sottomenu con tutte le azioni (autocompletamento — se ⇥ non è assegnato alle Universal Actions di Alfred)",
 k_ql="Anteprima Quick Look della pagina dell'icona",
 ctl_p="`nounctl`: accesso, stato, arresto/riavvio del browser in background, reinstallazione, log.",
 h_how="Come funziona",
 how_p1="Un demone Node/[Playwright](https://playwright.dev) ([`workflow/server.mjs`](workflow/server.mjs)) gira in background con un Chromium invisibile e un profilo persistente. La ricerca interroga l'API interna del sito (senza bisogno di account); il download passa per la mutation GraphQL `downloadIcon` con la tua sessione — il file arriva in base64, viene ripulito, poi salvato o copiato. Il demone si ferma dopo 3 ore di inattività e riparte su richiesta.",
 how_p2="Nessuna credenziale passa per il workflow: l'accesso avviene a mano nella finestra Chrome e i cookie restano nel profilo locale. Questa modalità automatizza la tua stessa sessione, per uso personale — resta nei limiti del tuo abbonamento e dei termini di servizio del sito.",
 h_dev="Sviluppo",
 c_zip="impacchetta il workflow", c_icon="rigenera workflow/icon.png", c_shots="rigenera gli screenshot", c_readmes="rigenera tutti i README", c_buttons="rigenera i pulsanti di download",
 dev1="`workflow/` — sorgenti: `info.plist`, script Python (solo stdlib), il demone `server.mjs`, `i18n.py` (9 lingue)",
 dev2="Il demone espone una piccola API HTTP locale (`/search`, `/download`, `/login`, `/status`, `/quit`) su 127.0.0.1",
 dev3="`dist/` — il pacchetto installabile",
 h_refs="Riferimenti", ref_docs="Documentazione dei workflow", ref_api="API ufficiale", ref_terms="Licenze",
 h_license="Licenza",
 license_p="MIT. Le icone restano soggette alle licenze The Noun Project (CC BY o pubblico dominio, abbonamento ove applicabile).",
 footer="Realizzato da <a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · Issue e PR benvenute",
)
T["pt"] = dict(
 title="Pesquisar e descarregar ícones do Noun Project",
 btn_alt="Descarregar o workflow",
 pitch="Pesquisa entre milhões de pictogramas do Noun Project e obtém o SVG ou o PNG sem largar o teclado.",
 tagline="Escreve `noun casa`, escolhe, prime **⏎**. O ficheiro fica na tua pasta — limpo, no tamanho certo.",
 alt_usage="Pesquisa «noun maison» no Alfred", alt_settings="Configuração do workflow",
 h_what="O que faz",
 f1_t="Pesquisa instantânea", f1_d="resultados com miniaturas; os ícones do domínio público aparecem primeiro, marcados com 🟢",
 f2_t="Uma grelha completa de atalhos", f2_d="⏎ descarrega o formato padrão, ⌥ muda para o outro, ⇧ copia em vez de guardar, ⌃ aponta para a menção de atribuição (.txt) e ⌘ combina-os — até ⌘⌥⇧⌃⏎, que copia tudo de seguida",
 f3_t="Fluxo de opções", f3_d="o submenu ▸ (autocompletar ⇥) lista as doze ações mais um fluxo guiado: formato → tamanho → pasta de destino",
 f4_t="Atribuição sempre à mão", f4_d="a menção de atribuição pode ser guardada em .txt ou copiada, sozinha ou juntamente com a imagem (as cópias sucessivas ficam todas no histórico da área de transferência)",
 f5_t="Limpeza", f5_d="a menção «Created by…» incrustada nos ficheiros gratuitos é removida (PNG recortado, texto retirado do código SVG); a licença CC BY passa então a exigir um crédito noutro lugar — ⇧⌃⏎ copia-o",
 f6_t="A tua própria sessão", f6_d="um Chrome invisível em segundo plano usa a tua conta thenounproject.com — catálogo completo, consoante a tua subscrição",
 f7_t="Localizado", f7_d="interface e notificações seguem o idioma do teu macOS (inglês, francês, alemão, espanhol, italiano, português, japonês, chinês, grego)",
 h_install="Instalação",
 inst1="Descarrega `The-Noun-Project.alfredworkflow` e faz duplo clique",
 inst2="Instala o Node.js se necessário: `brew install node` (o Python 3 vem com as Command Line Tools: `xcode-select --install`)",
 inst3="Lança uma primeira pesquisa — `noun casa` — o Playwright e o Chromium instalam-se sozinhos (alguns minutos, uma única vez)",
 inst4="Escreve `nounctl` → «Iniciar sessão»: abre-se uma janela do Chrome, autentica-te no site e ela fecha-se sozinha. A sessão persiste num perfil dedicado, separado do teu navegador habitual",
 requires="Requer [Alfred 5](https://www.alfredapp.com) com o [Powerpack](https://www.alfredapp.com/powerpack/).",
 h_config="Configuração",
 config_p="Backend (Navegador ou API oficial), formato padrão (SVG ou PNG — o outro passa a ser o «alternativo»), palavra-chave, pasta de descargas, tamanho PNG padrão, cor, número de resultados, limpeza da menção, mostrar no Finder. Em modo API (chave/segredo em [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/)), o acesso gratuito limita as descargas ao domínio público.",
 h_keys="Atalhos", key_col="Tecla", action_col="Ação",
 k_enter="Descarregar o formato padrão",
 k_alt="Descarregar o formato alternativo",
 k_ctrl="Descarregar a menção de atribuição em .txt",
 k_shift="Copiar o formato padrão para a área de transferência",
 k_shift_alt="Copiar o formato alternativo",
 k_shift_ctrl="Copiar a menção de atribuição",
 k_cmd="Descarregar a menção de atribuição + o formato padrão",
 k_cmd_alt="Descarregar a menção de atribuição + o formato alternativo",
 k_cmd_shift="Copiar a menção de atribuição, depois o formato padrão",
 k_cmd_shift_alt="Copiar a menção de atribuição, depois o formato alternativo",
 k_cmd_alt_ctrl="Descarregar os dois formatos + a menção de atribuição",
 k_all="Copiar a menção de atribuição, o alternativo e depois o formato padrão",
 k_tab="Submenu com todas as ações (autocompletar — se ⇥ não estiver atribuída às Universal Actions do Alfred)",
 k_ql="Pré-visualização Quick Look da página do ícone",
 ctl_p="`nounctl`: iniciar sessão, estado, parar/reiniciar o navegador de fundo, reinstalação, registos.",
 h_how="Como funciona",
 how_p1="Um daemon Node/[Playwright](https://playwright.dev) ([`workflow/server.mjs`](workflow/server.mjs)) corre em segundo plano com um Chromium invisível e um perfil persistente. A pesquisa consulta a API interna do site (sem conta); a descarga passa pela mutação GraphQL `downloadIcon` com a tua sessão — o ficheiro chega em base64, é limpo e depois guardado ou copiado. O daemon encerra-se após 3 h de inatividade e reinicia a pedido.",
 how_p2="Nenhuma credencial passa pelo workflow: a autenticação faz-se à mão na janela do Chrome e os cookies ficam no perfil local. Este modo automatiza a tua própria sessão, para uso pessoal — mantém-te dentro dos limites da tua subscrição e dos termos de utilização do site.",
 h_dev="Desenvolvimento",
 c_zip="empacota o workflow", c_icon="regenera workflow/icon.png", c_shots="regenera as capturas de ecrã", c_readmes="regenera todos os README", c_buttons="regenera os botões de descarga",
 dev1="`workflow/` — fontes: `info.plist`, scripts Python (apenas stdlib), o daemon `server.mjs`, `i18n.py` (9 idiomas)",
 dev2="O daemon expõe uma pequena API HTTP local (`/search`, `/download`, `/login`, `/status`, `/quit`) em 127.0.0.1",
 dev3="`dist/` — o pacote instalável",
 h_refs="Referências", ref_docs="Documentação de workflows", ref_api="API oficial", ref_terms="Licenças",
 h_license="Licença",
 license_p="MIT. Os ícones continuam sujeitos às licenças do The Noun Project (CC BY ou domínio público, subscrição quando aplicável).",
 footer="Feito por <a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · Issues e PRs bem-vindos",
)
T["ja"] = dict(
 title="Noun Project のアイコンを検索してダウンロード",
 btn_alt="ワークフローをダウンロード",
 pitch="数百万点の Noun Project アイコンを検索し、キーボードから手を離さずに SVG や PNG を取得。",
 tagline="`noun maison` と入力して選び、**⏎**。ファイルは指定のフォルダに、クリーンな状態で、ちょうどよいサイズで届きます。",
 alt_usage="Alfred での「noun maison」検索", alt_settings="ワークフローの設定画面",
 h_what="できること",
 f1_t="即時検索", f1_d="サムネイル付きの結果を表示。パブリックドメインのアイコンが 🟢 付きで先頭に並びます",
 f2_t="組み合わせ自在のショートカット", f2_d="⏎ で既定の形式をダウンロード、⌥ でもう一方の形式に切り替え、⇧ で保存の代わりにコピー、⌃ で帰属表示（.txt）を対象に、そして ⌘ でそれらを組み合わせ — ⌘⌥⇧⌃⏎ ならすべてを続けてコピーします",
 f3_t="オプションのフロー", f3_d="▸ サブメニュー（⇥ で自動補完）には 12 のアクションすべてに加え、ガイド付きフロー（形式 → サイズ → 保存先フォルダ）が並びます",
 f4_t="帰属表示もすぐ手元に", f4_d="帰属表示は .txt として保存もコピーも可能 — 単独でも画像と一緒でも（連続したコピーはすべてクリップボードの履歴に残ります）",
 f5_t="クリーンアップ", f5_d="無料ファイルに埋め込まれた「Created by…」の表記を除去します（PNG はトリミング、SVG はコードからテキストを削除）。その場合 CC BY では別の場所でのクレジット表記が必要になります — ⇧⌃⏎ でコピーできます",
 f6_t="あなた自身のセッション", f6_d="バックグラウンドの不可視の Chrome があなたの thenounproject.com アカウントを使用 — 契約プランに応じてフルカタログにアクセスできます",
 f7_t="多言語対応", f7_d="インターフェースと通知は macOS の言語に追随します（英語・フランス語・ドイツ語・スペイン語・イタリア語・ポルトガル語・日本語・中国語・ギリシャ語）",
 h_install="インストール",
 inst1="`The-Noun-Project.alfredworkflow` をダウンロードしてダブルクリック",
 inst2="必要なら Node.js をインストール：`brew install node`（Python 3 は Command Line Tools に含まれます：`xcode-select --install`）",
 inst3="はじめての検索 — `noun maison` — を実行すると、Playwright と Chromium が自動でインストールされます（数分、初回のみ）",
 inst4="`nounctl` と入力 → 「ログイン」を選択：Chrome のウインドウが開くのでサイト上でログインすると、ウインドウは自動で閉じます。セッションは普段のブラウザとは別の専用プロファイルに保持されます",
 requires="[Alfred 5](https://www.alfredapp.com) と [Powerpack](https://www.alfredapp.com/powerpack/) が必要です。",
 h_config="設定",
 config_p="バックエンド（ブラウザまたは公式 API）、既定の形式（SVG または PNG — もう一方が「代替」になります）、キーワード、ダウンロード先フォルダ、PNG の既定サイズ、色、結果件数、表記のクリーンアップ、Finder での表示。API モード（キー／シークレットは [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/) で取得）の場合、無料プランではダウンロードがパブリックドメインに限られます。",
 h_keys="ショートカット", key_col="キー", action_col="動作",
 k_enter="既定の形式をダウンロード",
 k_alt="代替形式をダウンロード",
 k_ctrl="帰属表示を .txt でダウンロード",
 k_shift="既定の形式をクリップボードにコピー",
 k_shift_alt="代替形式をコピー",
 k_shift_ctrl="帰属表示をコピー",
 k_cmd="帰属表示 + 既定の形式をダウンロード",
 k_cmd_alt="帰属表示 + 代替形式をダウンロード",
 k_cmd_shift="帰属表示、続けて既定の形式をコピー",
 k_cmd_shift_alt="帰属表示、続けて代替形式をコピー",
 k_cmd_alt_ctrl="両方の形式 + 帰属表示をダウンロード",
 k_all="帰属表示、代替形式、最後に既定の形式をコピー",
 k_tab="全アクションのサブメニュー（自動補完 — ⇥ が Alfred の Universal Actions に割り当てられていない場合）",
 k_ql="アイコンページを Quick Look でプレビュー",
 ctl_p="`nounctl`：ログイン、状態確認、バックグラウンドブラウザの停止／再起動、再インストール、ログの表示。",
 h_how="仕組み",
 how_p1="Node/[Playwright](https://playwright.dev) のデーモン（[`workflow/server.mjs`](workflow/server.mjs)）が、不可視の Chromium と永続プロファイルとともにバックグラウンドで動作します。検索はサイトの内部 API を照会し（アカウント不要）、ダウンロードはあなたのセッションで GraphQL ミューテーション `downloadIcon` を実行 — ファイルは base64 で届き、クリーンアップされたのち保存またはコピーされます。デーモンは 3 時間操作がないと停止し、必要になれば再起動します。",
 how_p2="認証情報がワークフローを経由することはありません：ログインは Chrome のウインドウで手動で行い、Cookie はローカルのプロファイルに残ります。これはあなた自身のセッションを個人利用のために自動化するものです — 契約プランとサイトの利用規約の範囲内でお使いください。",
 h_dev="開発",
 c_zip="ワークフローをパッケージ化", c_icon="workflow/icon.png を再生成", c_shots="スクリーンショットを再生成", c_readmes="README をすべて再生成", c_buttons="ダウンロードボタンを再生成",
 dev1="`workflow/` — ソース一式：`info.plist`、Python スクリプト（標準ライブラリのみ）、デーモン `server.mjs`、`i18n.py`（9 言語）",
 dev2="デーモンは 127.0.0.1 上に小さなローカル HTTP API（`/search`、`/download`、`/login`、`/status`、`/quit`）を公開します",
 dev3="`dist/` — インストール可能なパッケージ",
 h_refs="参考リンク", ref_docs="ワークフローのドキュメント", ref_api="公式 API", ref_terms="ライセンス",
 h_license="ライセンス",
 license_p="MIT。アイコン自体には引き続き The Noun Project のライセンス（CC BY またはパブリックドメイン、該当する場合は有料プラン）が適用されます。",
 footer="作者：<a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · Issue や PR を歓迎します",
)
T["zh"] = dict(
 title="搜索并下载 Noun Project 图标",
 btn_alt="下载工作流",
 pitch="在 Noun Project 的数百万个图标中搜索，不离开键盘即可获取 SVG 或 PNG。",
 tagline="输入 `noun house`，选中，按 **⏎**。文件已在你的文件夹里——干净，尺寸正好。",
 alt_usage="在 Alfred 中搜索“noun maison”", alt_settings="工作流设置",
 h_what="功能",
 f1_t="即时搜索", f1_d="结果带缩略图；公共领域图标排在最前，并标注 🟢",
 f2_t="一整套组合快捷键", f2_d="⏎ 下载默认格式，⌥ 切换到另一种格式，⇧ 改为复制而非保存，⌃ 针对署名信息（.txt），⌘ 负责组合——直到 ⌘⌥⇧⌃⏎ 一口气复制全部内容",
 f3_t="选项流程", f3_d="▸ 子菜单（⇥ 自动补全）列出全部十二个操作，外加一个引导流程：格式 → 尺寸 → 目标文件夹",
 f4_t="署名信息随手可得", f4_d="署名信息可保存为 .txt 或复制，可单独操作，也可与图像一起（连续复制的内容都会保留在剪贴板历史中）",
 f5_t="自动清理", f5_d="免费文件中内嵌的“Created by…”字样会被去除（PNG 裁剪，SVG 代码中的文字删除）；CC BY 许可因此要求在别处注明出处——⇧⌃⏎ 即可复制署名信息",
 f6_t="个人会话", f6_d="后台一个隐形 Chrome 使用你的 thenounproject.com 账户——完整目录，范围取决于你的订阅",
 f7_t="本地化", f7_d="界面与通知跟随 macOS 系统语言（英语、法语、德语、西班牙语、意大利语、葡萄牙语、日语、中文、希腊语）",
 h_install="安装",
 inst1="下载 `The-Noun-Project.alfredworkflow` 并双击",
 inst2="如有需要安装 Node.js：`brew install node`（Python 3 由 Command Line Tools 提供：`xcode-select --install`）",
 inst3="进行第一次搜索——`noun house`——Playwright 与 Chromium 会自动安装（几分钟，仅需一次）",
 inst4="输入 `nounctl` → “登录”：会弹出一个 Chrome 窗口，在网站上完成登录后窗口自动关闭。会话保存在独立的专用配置文件中，与你日常使用的浏览器互不干扰",
 requires="需要 [Alfred 5](https://www.alfredapp.com) 及 [Powerpack](https://www.alfredapp.com/powerpack/)。",
 h_config="设置",
 config_p="后端（浏览器或官方 API）、默认格式（SVG 或 PNG——另一种即为“备用”格式）、关键词、下载文件夹、默认 PNG 尺寸、颜色、结果数量、署名清理、在 Finder 中显示。API 模式下（在 [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/) 获取 key/secret），免费额度只能下载公共领域的图标。",
 h_keys="快捷键", key_col="按键", action_col="操作",
 k_enter="下载默认格式",
 k_alt="下载备用格式",
 k_ctrl="将署名信息下载为 .txt",
 k_shift="复制默认格式到剪贴板",
 k_shift_alt="复制备用格式",
 k_shift_ctrl="复制署名信息",
 k_cmd="下载署名信息 + 默认格式",
 k_cmd_alt="下载署名信息 + 备用格式",
 k_cmd_shift="先复制署名信息，再复制默认格式",
 k_cmd_shift_alt="先复制署名信息，再复制备用格式",
 k_cmd_alt_ctrl="下载两种格式 + 署名信息",
 k_all="依次复制署名信息、备用格式和默认格式",
 k_tab="包含全部操作的子菜单（自动补全——若 ⇥ 未绑定到 Alfred 的 Universal Actions）",
 k_ql="Quick Look 预览图标页面",
 ctl_p="`nounctl`：登录、状态、停止/重启后台浏览器、重新安装、查看日志。",
 h_how="工作原理",
 how_p1="一个 Node/[Playwright](https://playwright.dev) 守护进程（[`workflow/server.mjs`](workflow/server.mjs)）在后台运行，带一个隐形 Chromium 和持久化的浏览器配置文件。搜索调用网站的内部 API（无需账户）；下载则携带你的会话执行 GraphQL mutation `downloadIcon`——文件以 base64 形式返回，经清理后保存或复制。守护进程闲置 3 小时后自动退出，需要时按需重启。",
 how_p2="任何账号密码都不会经过工作流：登录由你在 Chrome 窗口中手动完成，Cookie 只保存在本地配置文件里。此模式只是自动化你自己的会话、供你个人使用——请遵守你的订阅范围与网站的服务条款。",
 h_dev="开发",
 c_zip="打包工作流", c_icon="重新生成 workflow/icon.png", c_shots="重新生成截图", c_readmes="重新生成所有 README", c_buttons="重新生成下载按钮",
 dev1="`workflow/` —— 源码：`info.plist`、Python 脚本（仅标准库）、守护进程 `server.mjs`、`i18n.py`（9 种语言）",
 dev2="守护进程在 127.0.0.1 上提供一个小型本地 HTTP API（`/search`、`/download`、`/login`、`/status`、`/quit`）",
 dev3="`dist/` —— 可安装的工作流包",
 h_refs="参考", ref_docs="工作流文档", ref_api="官方 API", ref_terms="许可条款",
 h_license="许可证",
 license_p="MIT。图标本身仍受 The Noun Project 相关许可约束（CC BY 或公共领域，如有订阅则按订阅许可）。",
 footer="作者：<a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · 欢迎提交 Issue 和 PR",
)
T["el"] = dict(
 title="Αναζήτηση και λήψη εικονιδίων του Noun Project",
 btn_alt="Λήψη του workflow",
 pitch="Αναζήτησε ανάμεσα σε εκατομμύρια εικονίδια του Noun Project και πάρε το SVG ή το PNG χωρίς να αφήσεις το πληκτρολόγιο.",
 tagline="Πληκτρολόγησε `noun maison`, διάλεξε, πάτα **⏎**. Το αρχείο φτάνει στον φάκελό σου — καθαρό, στο σωστό μέγεθος.",
 alt_usage="Αναζήτηση «noun maison» στο Alfred", alt_settings="Οι ρυθμίσεις του workflow",
 h_what="Τι κάνει",
 f1_t="Στιγμιαία αναζήτηση", f1_d="αποτελέσματα με μικρογραφίες· τα εικονίδια κοινού κτήματος έρχονται πρώτα, με σήμανση 🟢",
 f2_t="Ένα ολόκληρο πλέγμα συντομεύσεων", f2_d="το ⏎ κατεβάζει την προεπιλεγμένη μορφή, το ⌥ περνά στην άλλη, το ⇧ αντιγράφει αντί να αποθηκεύει, το ⌃ στοχεύει την αναφορά απόδοσης (.txt) και το ⌘ τα συνδυάζει — μέχρι το ⌘⌥⇧⌃⏎ που τα αντιγράφει όλα στη σειρά",
 f3_t="Ροή επιλογών", f3_d="το υπομενού ▸ (αυτόματη συμπλήρωση με ⇥) παραθέτει και τις δώδεκα ενέργειες συν μια καθοδηγούμενη ροή: μορφή → μέγεθος → φάκελος προορισμού",
 f4_t="Αναφορά απόδοσης στο χέρι", f4_d="η γραμμή αναφοράς αποθηκεύεται σε .txt ή αντιγράφεται, μόνη της ή μαζί με την εικόνα (οι διαδοχικές αντιγραφές μένουν όλες στο ιστορικό του προχείρου)",
 f5_t="Καθάρισμα", f5_d="η ενσωματωμένη ένδειξη «Created by…» στα δωρεάν αρχεία αφαιρείται (το PNG περικόπτεται, το κείμενο διαγράφεται από τον κώδικα SVG)· η άδεια CC BY απαιτεί τότε αναφορά απόδοσης αλλού — το ⇧⌃⏎ την αντιγράφει",
 f6_t="Προσωπική συνεδρία", f6_d="ένα αόρατο Chrome στο παρασκήνιο χρησιμοποιεί τον λογαριασμό σου στο thenounproject.com — πλήρης κατάλογος, ανάλογα με τη συνδρομή σου",
 f7_t="Στη γλώσσα σου", f7_d="διεπαφή και ειδοποιήσεις ακολουθούν τη γλώσσα του macOS σου (Αγγλικά, Γαλλικά, Γερμανικά, Ισπανικά, Ιταλικά, Πορτογαλικά, Ιαπωνικά, Κινεζικά, Ελληνικά)",
 h_install="Εγκατάσταση",
 inst1="Κατέβασε το `The-Noun-Project.alfredworkflow` και κάνε διπλό κλικ πάνω του",
 inst2="Εγκατέστησε το Node.js αν χρειάζεται: `brew install node` (η Python 3 έρχεται με τα Command Line Tools: `xcode-select --install`)",
 inst3="Κάνε μια πρώτη αναζήτηση — `noun maison` — το Playwright και το Chromium εγκαθίστανται μόνα τους (λίγα λεπτά, μία μόνο φορά)",
 inst4="Πληκτρολόγησε `nounctl` → «Σύνδεση»: ανοίγει ένα παράθυρο Chrome, συνδέσου στον ιστότοπο, κλείνει μόνο του. Η συνεδρία διατηρείται σε ειδικό προφίλ, ξεχωριστό από τον συνηθισμένο σου περιηγητή",
 requires="Απαιτεί [Alfred 5](https://www.alfredapp.com) με το [Powerpack](https://www.alfredapp.com/powerpack/).",
 h_config="Ρυθμίσεις",
 config_p="Backend (Περιηγητής ή επίσημο API), προεπιλεγμένη μορφή (SVG ή PNG — η άλλη γίνεται η «εναλλακτική»), λέξη-κλειδί, φάκελος λήψης, προεπιλεγμένο μέγεθος PNG, χρώμα, αριθμός αποτελεσμάτων, καθάρισμα της ένδειξης, εμφάνιση στο Finder. Σε λειτουργία API (κλειδί/μυστικό στο [thenounproject.com/developers/apps](https://thenounproject.com/developers/apps/)), η δωρεάν πρόσβαση περιορίζει τις λήψεις στο κοινό κτήμα.",
 h_keys="Συντομεύσεις", key_col="Πλήκτρο", action_col="Ενέργεια",
 k_enter="Λήψη της προεπιλεγμένης μορφής",
 k_alt="Λήψη της εναλλακτικής μορφής",
 k_ctrl="Λήψη της αναφοράς απόδοσης σε .txt",
 k_shift="Αντιγραφή της προεπιλεγμένης μορφής στο πρόχειρο",
 k_shift_alt="Αντιγραφή της εναλλακτικής μορφής",
 k_shift_ctrl="Αντιγραφή της αναφοράς απόδοσης",
 k_cmd="Λήψη αναφοράς απόδοσης + προεπιλεγμένης μορφής",
 k_cmd_alt="Λήψη αναφοράς απόδοσης + εναλλακτικής μορφής",
 k_cmd_shift="Αντιγραφή της αναφοράς απόδοσης, έπειτα της προεπιλεγμένης μορφής",
 k_cmd_shift_alt="Αντιγραφή της αναφοράς απόδοσης, έπειτα της εναλλακτικής μορφής",
 k_cmd_alt_ctrl="Λήψη και των δύο μορφών + της αναφοράς απόδοσης",
 k_all="Αντιγραφή της αναφοράς απόδοσης, της εναλλακτικής, έπειτα της προεπιλεγμένης μορφής",
 k_tab="Υπομενού με όλες τις ενέργειες (αυτόματη συμπλήρωση — αν το ⇥ δεν είναι δεσμευμένο στα Universal Actions του Alfred)",
 k_ql="Προεπισκόπηση Quick Look της σελίδας του εικονιδίου",
 ctl_p="`nounctl`: σύνδεση, κατάσταση, διακοπή/επανεκκίνηση του περιηγητή παρασκηνίου, επανεγκατάσταση, αρχεία καταγραφής.",
 h_how="Πώς λειτουργεί",
 how_p1="Ένας δαίμονας Node/[Playwright](https://playwright.dev) ([`workflow/server.mjs`](workflow/server.mjs)) τρέχει στο παρασκήνιο με ένα αόρατο Chromium και μόνιμο προφίλ. Η αναζήτηση περνά από το εσωτερικό API του ιστότοπου (χωρίς λογαριασμό)· η λήψη γίνεται μέσω του GraphQL mutation `downloadIcon` με τη συνεδρία σου — το αρχείο φτάνει σε base64, καθαρίζεται, έπειτα αποθηκεύεται ή αντιγράφεται. Ο δαίμονας σταματά μετά από 3 ώρες αδράνειας και επανεκκινεί όταν χρειαστεί.",
 how_p2="Κανένα διαπιστευτήριο δεν περνά από το workflow: η σύνδεση γίνεται με το χέρι στο παράθυρο του Chrome, τα cookies μένουν στο τοπικό προφίλ. Αυτό αυτοματοποιεί τη δική σου συνεδρία, για προσωπική σου χρήση — μείνε μέσα στα όρια της συνδρομής σου και των όρων χρήσης του ιστότοπου.",
 h_dev="Ανάπτυξη",
 c_zip="πακετάρει το workflow", c_icon="αναδημιουργεί το workflow/icon.png", c_shots="αναδημιουργεί τα στιγμιότυπα οθόνης", c_readmes="αναδημιουργεί όλα τα README", c_buttons="αναδημιουργεί τα κουμπιά λήψης",
 dev1="`workflow/` — οι πηγές: `info.plist`, scripts Python (μόνο stdlib), ο δαίμονας `server.mjs`, `i18n.py` (9 γλώσσες)",
 dev2="Ο δαίμονας εκθέτει ένα μικρό τοπικό HTTP API (`/search`, `/download`, `/login`, `/status`, `/quit`) στη 127.0.0.1",
 dev3="`dist/` — το εγκαταστάσιμο πακέτο",
 h_refs="Αναφορές", ref_docs="Τεκμηρίωση workflows", ref_api="Επίσημο API", ref_terms="Άδειες",
 h_license="Άδεια",
 license_p="MIT. Τα εικονίδια εξακολουθούν να υπόκεινται στις άδειες του The Noun Project (CC BY ή κοινό κτήμα, συνδρομή κατά περίπτωση).",
 footer="Από τον <a href='https://damiencuvillier.com' target='_blank' rel='noopener'>Damien</a> · Issues και PRs ευπρόσδεκτα",
)

for code, _, _ in LANGS:
    body = TEMPLATE.format(nav=nav(code), code=code, **T[code])
    with open(os.path.join(OUT, fname(code)), "w") as f:
        f.write(body)
    print("→ " + fname(code))
