const OWNER_NAMES = ['Toll Brothers Holdings','M/I Homes LLC','Pulte Group','Bank of Ann Arbor','Lennar Corp','NVR Inc','Taylor Morrison','Meritage Homes','Century Communities','Smith Family Trust','Johnson Land Holdings','Williams Development','Davis Realty Group','Municipal Land Bank','Thompson Estates','Martin Property LLC','Anderson Farm Trust','Heritage Homes Inc','Great Lakes Dev','Washtenaw Housing Auth'];
const CITIES = ['Ann Arbor','Saline','Dexter','Chelsea','Ypsilanti','Milan','Manchester','Scio Twp','Pittsfield Twp','Northfield Twp','Lima Twp','Lodi Twp','Webster Twp','Superior Twp','Salem Twp','York Twp','Augusta Twp','Bridgewater Twp','Freedom Twp','Sylvan Twp'];
const SIGNALS = ['HIGHEST','HIGH','MEDIUM','LOW','NONE'];
const CONCS = ['TIGHT','MODERATE','SPREAD','SCATTERED'];

const rand = (a) => a[Math.floor(Math.random() * a.length)];

function generateClusters(count = 60) {
  const clusters = [];
  for (let i = 0; i < count; i++) {
    const lots = i < 3 ? [146, 99, 59][i] : Math.floor(Math.random() * 40) + 2;
    const acres = Math.floor(lots * (3 + Math.random() * 15));
    const sig = i < 5 ? SIGNALS[0] : i < 12 ? SIGNALS[1] : i < 25 ? SIGNALS[2] : i < 40 ? SIGNALS[3] : SIGNALS[4];
    const margin = sig === 'HIGHEST' ? 25 + Math.random() * 15 : sig === 'HIGH' ? 15 + Math.random() * 12 : sig === 'MEDIUM' ? 5 + Math.random() * 12 : sig === 'LOW' ? -5 + Math.random() * 15 : -10 + Math.random() * 10;
    const tier = margin >= 25 ? 'A' : margin >= 15 ? 'B' : margin > 0 ? 'C' : 'X';
    const type = i < 20 ? 'owner' : i < 30 ? 'subdivision' : i < 45 ? 'proximity' : i < 52 ? 'agent' : 'office';

    clusters.push({
      id: `cl-${i}`,
      name: i < 20 ? OWNER_NAMES[i] : type === 'subdivision' ? `${rand(CITIES)} Phase ${Math.floor(Math.random() * 5) + 1}` : type === 'agent' ? `${rand(['RE/MAX','Keller Williams','Howard Hanna','Coldwell Banker','Century 21'])} ${rand(CITIES)}` : type === 'office' ? `${rand(CITIES)} Office Group` : `${rand(CITIES)} Cluster`,
      type, lots, acres, signal: sig, tier,
      margin: parseFloat(margin.toFixed(1)),
      conc: i < 8 ? CONCS[0] : i < 20 ? CONCS[1] : i < 40 ? CONCS[2] : CONCS[3],
      city: rand(CITIES),
      lat: 42.2 + Math.random() * 0.25,
      lng: -83.7 - Math.random() * 0.35,
      score: Math.floor(40 + Math.random() * 55),
      landVal: Math.floor(lots * (15000 + Math.random() * 45000)),
      hasListing: sig !== 'NONE' && Math.random() > 0.3,
      bis: Math.floor(20 + Math.random() * 75),
    });
  }
  return clusters;
}

export const CLUSTERS = generateClusters();
export { CITIES, SIGNALS, CONCS };
