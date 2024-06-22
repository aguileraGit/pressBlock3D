
## To Do
- [x] Create git
- [x] Write Library
- [ ] Look at Fn: parseSVG to make front end easier to use
- [ ] Add Fn to generate [SVG](https://cadquery.readthedocs.io/en/latest/importexport.html#exporting-svg) of final Block in 3D
- [ ] Should we be checking for paths that aren't closed? I believe svgpathtools has a way to check.
- [ ] Look at SVGs that aren't working in 'jupyter-cadquery-modified' folder. Unsure if it's related to above.
- [ ] Push to Streamlit(?)
- [ ] Add in other SVG components (text, rect, lines). See below.

## Think about DB backend.
Design based. User would create a design. Then add SVG and set parameters. Once happy with results, the user would save it. 

In the backend, creating the design would create a MongoDB document with an id (default action) inside a Collection called Designs. When the user saves it, the values are stored to the Document. The id is all attached to a Collection callued Users. Looking up a User, will show all their designs in the Designs Collection.

Once a design is printed, it shouldn't be editable. There should be a way to quickly create a clone.


Think about putting identifier - shorter UUID to tie the device to the Design Collection.


## Other SVG Components
This is a challenge since Dov's current code depend on svgpathtools which seems to only parse Paths. (Needs to be verified)

In theory could parse again using other libraries. 
- Text would rely on font in SVG.
- Lines, circles, rect, etc could be done with a sweep.
