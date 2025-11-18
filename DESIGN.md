# Design System - LKW Bot Platform

## 🎨 Design-Philosophie

**Modern • Minimalistisch • User-Friendly**

- Klares, aufgeräumtes Interface
- Konsistente Farben und Abstände
- Responsive Design (Mobile-First)
- Smooth Animationen und Übergänge
- Intuitive Navigation

## 🎭 Farbschema

### Primärfarben (Blau)
```
primary-50:  #f0f9ff  (sehr hell)
primary-100: #e0f2fe
primary-200: #bae6fd
primary-300: #7dd3fc
primary-400: #38bdf8
primary-500: #0ea5e9  (Hauptfarbe)
primary-600: #0284c7  (Hover)
primary-700: #0369a1
primary-800: #075985
primary-900: #0c4a6e  (dunkel)
```

### Status-Farben
```
Success: green-500  #10b981
Error:   red-500    #ef4444
Warning: yellow-500 #eab308
Info:    blue-500   #3b82f6
```

### Neutrale Farben
```
Background: slate-50  #f8fafc
Cards:      white     #ffffff
Border:     slate-200 #e2e8f0
Text:       slate-900 #0f172a
Muted:      slate-500 #64748b
```

## 📐 Layout-Komponenten

### 1. Cards
```html
<div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
    <!-- Content -->
</div>
```

### 2. Buttons

**Primary Button:**
```html
<button class="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2.5 px-6 rounded-lg 
               shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all">
    Button Text
</button>
```

**Secondary Button:**
```html
<button class="bg-white hover:bg-slate-50 text-slate-700 font-semibold py-2.5 px-6 rounded-lg 
               border-2 border-slate-200 hover:border-primary-500 transition-all">
    Button Text
</button>
```

**Danger Button:**
```html
<button class="bg-red-600 hover:bg-red-700 text-white font-semibold py-2.5 px-6 rounded-lg 
               shadow-md hover:shadow-lg transition-all">
    Button Text
</button>
```

**Success Button:**
```html
<button class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2.5 px-6 rounded-lg 
               shadow-md hover:shadow-lg transition-all">
    Button Text
</button>
```

### 3. Form Inputs
```html
<input type="text" 
       class="w-full px-4 py-3 rounded-lg border-2 border-slate-200 
              focus:border-primary-500 focus:ring-2 focus:ring-primary-200 
              outline-none transition-all"
       placeholder="Placeholder...">
```

### 4. Labels
```html
<label class="block text-sm font-semibold text-slate-700 mb-2">
    Label Text
</label>
```

### 5. Badges

**Status Badge:**
```html
<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium 
             bg-green-100 text-green-800">
    Aktiv
</span>
```

**Info Badge:**
```html
<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium 
             bg-blue-100 text-blue-800">
    15 Tage
</span>
```

### 6. Navigation Bar
```html
<nav class="bg-white shadow-md border-b border-slate-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
            <!-- Nav Items -->
        </div>
    </div>
</nav>
```

### 7. Sidebar
```html
<aside class="w-64 bg-white shadow-lg h-screen fixed left-0 top-0 overflow-y-auto">
    <div class="p-6">
        <!-- Sidebar Content -->
    </div>
</aside>
```

### 8. Dashboard Stats Card
```html
<div class="bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl shadow-lg p-6 text-white">
    <div class="flex items-center justify-between">
        <div>
            <p class="text-primary-100 text-sm font-medium">Titel</p>
            <p class="text-3xl font-bold mt-2">Wert</p>
        </div>
        <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
            <!-- Icon -->
        </div>
    </div>
</div>
```

### 9. Table
```html
<div class="overflow-x-auto rounded-lg border border-slate-200">
    <table class="min-w-full divide-y divide-slate-200">
        <thead class="bg-slate-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Header
                </th>
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-slate-200">
            <tr class="hover:bg-slate-50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                    Data
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

### 10. Modal/Dialog
```html
<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 p-6">
        <h3 class="text-xl font-bold text-slate-900 mb-4">Modal Titel</h3>
        <!-- Modal Content -->
        <div class="flex justify-end space-x-3 mt-6">
            <button class="px-4 py-2 rounded-lg border-2 border-slate-200 hover:bg-slate-50">
                Abbrechen
            </button>
            <button class="px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700">
                Bestätigen
            </button>
        </div>
    </div>
</div>
```

## 📱 Responsive Breakpoints

```
sm:  640px   (Smartphone)
md:  768px   (Tablet)
lg:  1024px  (Desktop)
xl:  1280px  (Large Desktop)
2xl: 1536px  (Extra Large)
```

Beispiel:
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Responsive Grid -->
</div>
```

## ✨ Animationen

### Hover Effects
```html
<!-- Button -->
class="transform hover:-translate-y-0.5 hover:shadow-lg transition-all"

<!-- Card -->
class="hover:shadow-xl transition-shadow duration-300"

<!-- Icon -->
class="hover:rotate-12 transition-transform"
```

### Transitions
```html
<!-- Fade In -->
class="transition-opacity duration-300 ease-in-out"

<!-- Slide In -->
class="transition-transform duration-300 ease-out"
```

## 🎯 Spacing System

```
p-2:  0.5rem (8px)
p-4:  1rem   (16px)
p-6:  1.5rem (24px)
p-8:  2rem   (32px)
p-12: 3rem   (48px)

gap-2: 0.5rem
gap-4: 1rem
gap-6: 1.5rem
```

## 🔤 Typography

### Headings
```html
<h1 class="text-4xl font-bold text-slate-900">Hauptüberschrift</h1>
<h2 class="text-3xl font-bold text-slate-900">Unterüberschrift</h2>
<h3 class="text-2xl font-semibold text-slate-800">Sektion</h3>
<h4 class="text-xl font-semibold text-slate-800">Kleinere Sektion</h4>
```

### Body Text
```html
<p class="text-base text-slate-700">Normaler Text</p>
<p class="text-sm text-slate-600">Kleinerer Text</p>
<p class="text-xs text-slate-500">Sehr kleiner Text</p>
```

## 🎨 Icons

Verwende **Heroicons** (kompatibel mit Tailwind):
- Kostenlos
- SVG-basiert
- Konsistenter Stil

Download: https://heroicons.com/

## 🌐 Beispiel: Login-Seite Layout

```html
<div class="min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full">
        <!-- Logo/Header Card -->
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold text-slate-900">LKW Bot</h1>
            <p class="text-slate-600 mt-2">Willkommen zurück</p>
        </div>
        
        <!-- Login Card -->
        <div class="bg-white rounded-xl shadow-xl p-8">
            <form>
                <!-- Form Content -->
            </form>
        </div>
        
        <!-- Footer Link -->
        <p class="text-center text-slate-600 text-sm mt-6">
            Noch kein Account? 
            <a href="#" class="text-primary-600 hover:text-primary-700 font-semibold">
                Registrieren
            </a>
        </p>
    </div>
</div>
```

## 🎭 Dark Mode (Optional für später)

Falls gewünscht, können wir später Dark Mode hinzufügen:
```html
<html class="dark">
<body class="bg-slate-900 dark:bg-slate-900">
    <div class="bg-white dark:bg-slate-800 text-slate-900 dark:text-white">
        <!-- Content -->
    </div>
</body>
</html>
```

## 📦 Verwendete Libraries

- **Tailwind CSS 3.x** (via CDN)
- **Alpine.js 3.x** (für interaktive Komponenten)
- **Heroicons** (Icons, optional)

---

**Ziel:** Ein professionelles, modernes Interface das Vertrauen schafft und einfach zu bedienen ist.