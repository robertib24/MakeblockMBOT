# Tutorial diagrame

## Optiunea 1: VS Code 

1. **Instaleaza extensia PlantUML**:
   - Deschide VS Code
   - Apasă `Ctrl+Shift+X` (Extensions)
   - Caută "PlantUML"
   - Instalează extensia de la "jebbs"

2. **Deschide fisierul**:
   - Deschide `arhitectura_sistem.puml` în VS Code
   - Apasa `Alt+D` pentru preview
   - Click dreapta -> "Export Current Diagram" -> PNG/SVG/PDF

## Optiunea 2: Online 

1. **Mergi pe**: http://www.plantuml.com/plantuml/uml/

2. **Copiază tot continutul** din fifierul `arhitectura_sistem.puml`

3. **Lipește în editor**

4. **Click pe "Submit"** - diagrama se generează automat

5. **Download**: Click dreapta pe imagine -> Save image as...

## Opțiunea 3: PlantText (Alternative)

1. **Mergi pe**: https://www.planttext.com/

2. **Copiaza continutul** fisierului .puml

3. **Click "Refresh"**

4. **Download PNG/SVG**

---

## Personalizare:

Poti modifica în fisierul `.puml`:

- **Culori**: din linia `BackgroundColor<<tip>>` 
- **Dimensiuni font**: din linia `FontSize`
- **Text în componente**: intre `[...]`
- **Note**: blocuri `note right/left/bottom`

---

## Troubleshooting:

**Eroare: "Java not found"**
→ Instaleaza Java pentru ca e necesar pentru PlantUML, altfel nu functioneaza

**Graficele arata urat**
→ Instaleaza Graphviz: https://graphviz.org/download/

**Preview nu se încarcă în VS Code**
→ `Ctrl+Shift+P` -> "PlantUML: Preview Current Diagram"


---

Succes!
