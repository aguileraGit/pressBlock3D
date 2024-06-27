
## To do
- [ ] Fix number of paths not showing up
- [ ] Estimated Height/Width showing up on different line
- [ ] Estimated Height/Width should propage to next section once SVG upload successful
- [ ] Need to add in fillet
- [ ] Uploading second file before setting values results in 2 SVGs processed on backend. Fix it.

- [ ] Should we be checking for paths that aren't closed? I believe svgpathtools has a way to check.
- [ ] Should be checking for SVGs with text and other non-supported commands to produce warning for user
- [ ] Need to look at globals and turbo to see how this is affected when moving to ngix or similar
- [ ] For X/Y padding, update function to return padding h/w as well


## To do later
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


## Document deployment process
Document things needed to be able to deploy this in a more professional way

## Pip
- Flask
- pip install git+https://github.com/CadQuery/cadquery.git@3451007f8eeb9d78e784ec8047ef69a5359ecb5e
- Other SVG libraries (svgparse?, svgpathtools, stl-numpy?, )
- Turbo
