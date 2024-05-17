
## To Do
- [x] Create git
- [ ] Write Library
- [ ] Should we be checking for paths that aren't closed? I believe svgpathtools has a way to check.
- [ ] Look at SVGs that aren't working in 'jupyter-cadquery-modified' folder. Unsure if it's related to above.
- [ ] Push to Streamlit(?)
- [ ] Add in other SVG components (text, rect, lines). See below.

Think about DB backend.

Think about putting identifier


## Other SVG Components
This is a challenge since Dov's current code depend on svgpathtools which seems to only parse Paths. (Needs to be verified)

In theory could parse again using other libraries. 
- Text would rely on font in SVG.
- Lines, circles, rect, etc could be done with a sweep.
