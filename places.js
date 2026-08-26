// Edit this file to change what shows on the map.
//
// Each entry:
//   name     required
//   park     "dl" (Disneyland) or "dca" (California Adventure)
//   land     free text, used to group the list
//   type     "food" | "ride" | "show" | "shop"
//   lat/lng  approximate — drag the pin on the map to fix, then use "Copy data file"
//   must     true = shows a star, appears in the "Must do" filter
//   note     free text, shows on the card and in the popup

window.PLACES = [
  // ---------- Disneyland Park ----------
  { name: "Jolly Holiday Bakery", park: "dl", land: "Main Street U.S.A.", type: "food", lat: 33.81169, lng: -117.91923, must: false, note: "Grapefruit cake. Good first-thing coffee stop." },
  { name: "Carnation Cafe", park: "dl", land: "Main Street U.S.A.", type: "food", lat: 33.81131, lng: -117.91875, must: false, note: "Sit-down breakfast, patio seating." },
  { name: "Bengal Barbecue", park: "dl", land: "Adventureland", type: "food", lat: 33.81174, lng: -117.92004, must: true, note: "Bacon-wrapped asparagus skewer." },
  { name: "The Tropical Hideaway", park: "dl", land: "Adventureland", type: "food", lat: 33.81201, lng: -117.92032, must: true, note: "Dole Whip with the shorter line." },
  { name: "Jungle Cruise", park: "dl", land: "Adventureland", type: "ride", lat: 33.81157, lng: -117.92024, must: false, note: "" },
  { name: "Indiana Jones Adventure", park: "dl", land: "Adventureland", type: "ride", lat: 33.81138, lng: -117.92064, must: true, note: "" },
  { name: "Blue Bayou", park: "dl", land: "New Orleans Square", type: "food", lat: 33.81232, lng: -117.92092, must: true, note: "Reservations open 60 days out. Book the moment they drop." },
  { name: "Cafe Orleans", park: "dl", land: "New Orleans Square", type: "food", lat: 33.81259, lng: -117.92112, must: false, note: "Monte Cristo without the Blue Bayou wait." },
  { name: "Mint Julep Bar", park: "dl", land: "New Orleans Square", type: "food", lat: 33.81271, lng: -117.92131, must: false, note: "Beignets. Cash-and-go window." },
  { name: "Pirates of the Caribbean", park: "dl", land: "New Orleans Square", type: "ride", lat: 33.81213, lng: -117.92078, must: true, note: "" },
  { name: "Haunted Mansion", park: "dl", land: "New Orleans Square", type: "ride", lat: 33.81294, lng: -117.92148, must: true, note: "Check whether Holiday overlay is up." },
  { name: "Rancho del Zocalo", park: "dl", land: "Frontierland", type: "food", lat: 33.81282, lng: -117.92042, must: false, note: "Big shaded patio. Best sit-down-ish lunch in the park." },
  { name: "Big Thunder Mountain", park: "dl", land: "Frontierland", type: "ride", lat: 33.81338, lng: -117.92064, must: false, note: "" },
  { name: "Harbour Galley", park: "dl", land: "Critter Country", type: "food", lat: 33.81352, lng: -117.92136, must: false, note: "Clam chowder bread bowl, quiet seating." },
  { name: "Ronto Roasters", park: "dl", land: "Galaxy's Edge", type: "food", lat: 33.81441, lng: -117.92271, must: true, note: "Ronto wrap. Best savory item in the park." },
  { name: "Docking Bay 7", park: "dl", land: "Galaxy's Edge", type: "food", lat: 33.81462, lng: -117.92318, must: false, note: "" },
  { name: "Oga's Cantina", park: "dl", land: "Galaxy's Edge", type: "food", lat: 33.81471, lng: -117.92283, must: true, note: "Reservation required. 45 min seating limit." },
  { name: "Rise of the Resistance", park: "dl", land: "Galaxy's Edge", type: "ride", lat: 33.81496, lng: -117.92341, must: true, note: "Buy Lightning Lane early or queue at rope drop." },
  { name: "Millennium Falcon: Smugglers Run", park: "dl", land: "Galaxy's Edge", type: "ride", lat: 33.81452, lng: -117.92238, must: false, note: "" },
  { name: "Red Rose Taverne", park: "dl", land: "Fantasyland", type: "food", lat: 33.81303, lng: -117.91979, must: false, note: "" },
  { name: "Matterhorn Bobsleds", park: "dl", land: "Fantasyland", type: "ride", lat: 33.81275, lng: -117.91848, must: false, note: "" },
  { name: "Peter Pan's Flight", park: "dl", land: "Fantasyland", type: "ride", lat: 33.81338, lng: -117.91941, must: false, note: "Line gets ugly fast. Go early or late." },
  { name: "Space Mountain", park: "dl", land: "Tomorrowland", type: "ride", lat: 33.81219, lng: -117.91713, must: true, note: "" },
  { name: "Galactic Grill", park: "dl", land: "Tomorrowland", type: "food", lat: 33.81232, lng: -117.91746, must: false, note: "" },
  { name: "Fireworks viewing", park: "dl", land: "Central Plaza", type: "show", lat: 33.81211, lng: -117.91897, must: true, note: "Stake out a spot on the hub ~45 min early." },

  // ---------- Disney California Adventure ----------
  { name: "Carthay Circle Lounge", park: "dca", land: "Buena Vista Street", type: "food", lat: 33.80672, lng: -117.91897, must: true, note: "Fried biscuits. Lounge takes walk-ups more often than upstairs." },
  { name: "Fiddler, Fifer & Practical Cafe", park: "dca", land: "Buena Vista Street", type: "food", lat: 33.80712, lng: -117.91876, must: false, note: "Starbucks. First stop on a DCA morning." },
  { name: "Flo's V8 Cafe", park: "dca", land: "Cars Land", type: "food", lat: 33.80461, lng: -117.91702, must: false, note: "" },
  { name: "Cozy Cone Motel", park: "dca", land: "Cars Land", type: "food", lat: 33.80478, lng: -117.91731, must: true, note: "Chili cone queso and the bacon mac cone." },
  { name: "Radiator Springs Racers", park: "dca", land: "Cars Land", type: "ride", lat: 33.80432, lng: -117.91652, must: true, note: "Highest-demand ride in either park." },
  { name: "Lamplight Lounge", park: "dca", land: "Pixar Pier", type: "food", lat: 33.80581, lng: -117.91612, must: true, note: "Lobster nachos. Book ahead, waterfront table if you can." },
  { name: "Incredicoaster", park: "dca", land: "Pixar Pier", type: "ride", lat: 33.80534, lng: -117.91512, must: false, note: "" },
  { name: "Toy Story Midway Mania", park: "dca", land: "Paradise Gardens", type: "ride", lat: 33.80438, lng: -117.91503, must: false, note: "" },
  { name: "San Fransokyo Square", park: "dca", land: "San Fransokyo Square", type: "food", lat: 33.80601, lng: -117.91688, must: true, note: "Bread bowls, Aunt Cass Cafe, good beer selection." },
  { name: "Pym Test Kitchen", park: "dca", land: "Avengers Campus", type: "food", lat: 33.80542, lng: -117.91982, must: false, note: "Oversized pretzel. More gimmick than meal." },
  { name: "Guardians of the Galaxy: Mission Breakout", park: "dca", land: "Avengers Campus", type: "ride", lat: 33.80621, lng: -117.91991, must: true, note: "" },
  { name: "Smokejumpers Grill", park: "dca", land: "Grizzly Peak", type: "food", lat: 33.80721, lng: -117.91762, must: false, note: "" },
  { name: "Soarin' Around the World", park: "dca", land: "Grizzly Peak", type: "ride", lat: 33.80774, lng: -117.91841, must: false, note: "" },
  { name: "World of Color viewing", park: "dca", land: "Paradise Gardens", type: "show", lat: 33.80551, lng: -117.91702, must: true, note: "Dining package is the low-stress option." }
];
