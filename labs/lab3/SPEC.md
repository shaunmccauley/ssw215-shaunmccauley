# SPEC: Developer Portfolio Welcome Page
## 1. Purpose & Scope
- A personal portfolio welcome page for Shaun McCauley, a sophomore software
engineering student.
- Non-Goals: no multi-page routing; no backend; no contact forms.
## 2. Invariants & Negative Constraints
- All styling MUST reside in `./style.css` (no inline style="..." attributes).
- The page MUST NOT load external CSS frameworks or CDNs (no Bootstrap, no Tailwind).
- The avatar image MUST use the relative path `./assets/avatar.jpg`.
- The layout MUST collapse into a single vertical column on screens narrower than 768px.
## 3. UI Content & Interface Contract
- Hero header: my full name "Shaun McCauley", the subtitle "Sophomore software engineering student at Stevens Institute of Technology.", and
this bio: "I enjoy working on both front-end and back-end, and I am learning React next. Away from the keyboard, I am hiking, cooking, or playing basketball and pickleball.".
- Action link: a button labelled "See my projects" that links to `#projects`.
- Projects section with id="projects": lists these items: NBA Player Stats Tracker, a command-line tool for looking up player stats; Autonomous Navigational Robot, a robot that finds its own way around; LeetCode Assistant (planned), a tool to help with studying practice problems.
- Social link: GitHub (https://github.com/shaunmccauley) MUST open in a new tab
(target="_blank").
## 4. Acceptance Checklist
- [x] Valid semantic HTML5: the page uses <header>, <main>, and <footer>.
- [x] The avatar image has width, height, and alt attributes.
- [x] No horizontal scrollbar when the browser is narrowed to 375px.
- [x] The GitHub link opens in a new tab and has rel="noopener".
- [x] No placeholder links: href="#" appears nowhere.
## 5. Audit Protocol
- Inspect the generated code line by line with `git diff --staged` before committing.