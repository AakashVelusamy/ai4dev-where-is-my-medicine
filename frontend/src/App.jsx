import React, { useState } from 'react';
import MapComponent from './components/MapComponent';
import {
  FileText,
  Camera,
  Search,
  Stethoscope,
  MapPin,
  Info,
  AlertCircle,
  Phone,
  Clock,
  ExternalLink,
  ChevronRight
} from 'lucide-react';

const App = () => {
  const [activeTab, setActiveTab] = useState('text');
  const [searchQuery, setSearchQuery] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedMedicine, setSelectedMedicine] = useState(null);
  const [pharmacies, setPharmacies] = useState([]);
  const [userLocation, setUserLocation] = useState(null);

  React.useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude
          });
        },
        (error) => {
          console.error("Error getting location:", error);
          // Default to Coimbatore if denied
          setUserLocation({ lat: 11.0168, lon: 76.9558 });
        }
      );
    }
  }, []);

  const tabs = [
    { id: 'text', icon: Search, label: 'Name' },
    { id: 'prescription', icon: FileText, label: 'Prescription' },
    { id: 'tablet', icon: Camera, label: 'Tablet Photo' },
    { id: 'symptoms', icon: Stethoscope, label: 'Symptoms' },
  ];

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSearch = async (e) => {
    if (e) e.preventDefault();

    if ((activeTab === 'text' || activeTab === 'symptoms') && !searchQuery.trim()) {
      alert("Please enter a search query.");
      return;
    }
    if ((activeTab === 'prescription' || activeTab === 'tablet') && !file) {
      alert("Please select a file to upload.");
      return;
    }

    setLoading(true);
    setResults(null);
    setPharmacies([]);

    try {
      const baseUrl = 'http://localhost:8000/api';
      let data = null;

      if (activeTab === 'text') {
        const res = await fetch(`${baseUrl}/search-medicine?q=${encodeURIComponent(searchQuery)}`);
        if (!res.ok) throw new Error("Medicine not found");
        data = await res.json();
      } else if (activeTab === 'symptoms') {
        const res = await fetch(`${baseUrl}/symptom-search?symptoms=${encodeURIComponent(searchQuery)}`);
        if (!res.ok) throw new Error("No medicines found for symptoms");
        data = await res.json();
      } else if (activeTab === 'prescription') {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`${baseUrl}/prescription`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error("Failed to process prescription");
        data = await res.json();
      } else if (activeTab === 'tablet') {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`${baseUrl}/tablet-photo`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error("Failed to process tablet photo");
        data = await res.json();
      }

      let bestMatch = null;
      let subs = [];

      if (activeTab === 'text' || activeTab === 'symptoms') {
        if (data.results?.length > 0) {
          bestMatch = data.results[0];
          subs = data.results.slice(1, 4).map(r => r.medicine_name);
        }
      } else {
        const meds = data.detected_medicines || [];
        if (meds.length > 0) {
          const detailRes = await fetch(`${baseUrl}/search-medicine?q=${encodeURIComponent(meds[0])}`);
          if (detailRes.ok) {
            const detailData = await detailRes.json();
            if (detailData.results?.length > 0) bestMatch = detailData.results[0];
          }
          subs = meds.slice(1, 4);
        }
      }

      if (bestMatch) {
        setResults({
          name: bestMatch.medicine_name,
          composition: bestMatch.composition,
          uses: bestMatch.uses,
          sideEffects: bestMatch.side_effects || "N/A",
          substitutes: subs.length > 0 ? subs : ["Consult Pharmacist"]
        });

        // Step 3: Find REAL pharmacies nearby
        try {
          const lat = userLocation?.lat || 11.0168; // Fallback to Coimbatore if no user location
          const lon = userLocation?.lon || 76.9558;

          const phRes = await fetch(`${baseUrl}/pharmacies-nearby?medicine=${encodeURIComponent(bestMatch.medicine_name)}&lat=${lat}&lon=${lon}`);
          if (phRes.ok) {
            const phData = await phRes.json();
            setPharmacies(phData.pharmacies || []);

            // If the original medicine is out of stock, use the substitutes returned from backend
            if (phData.status === "substitute_recommended") {
              setResults(prev => ({
                ...prev,
                substitutes: phData.substitutes || prev.substitutes
              }));
            }
          }
        } catch (err) {
          console.warn("Could not fetch pharmacies:", err);
        }
      } else {
        alert("No matches found.");
      }
    } catch (err) {
      console.error(err);
      alert(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center p-4 md:p-8">
      {/* Header */}
      <header className="w-full max-w-4xl mb-8 flex flex-col items-center">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-medic-500 rounded-2xl shadow-lg">
            <Stethoscope className="text-white w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">
            Where Is My <span className="text-medic-500">Medicine</span> ?
          </h1>
        </div>
        <p className="text-slate-500 text-center max-w-md">
          Identify medicines instantly and find the nearest availability.
        </p>
      </header>

      {/* Main Search Section */}
      <main className="w-full max-w-4xl glass-effect rounded-3xl shadow-xl overflow-hidden mb-8">
        <div className="flex border-b border-slate-100 bg-slate-50/50">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-4 flex flex-col items-center gap-1 transition-all
                ${activeTab === tab.id
                  ? 'bg-white text-medic-600 shadow-sm'
                  : 'text-slate-400 hover:text-slate-600'}`}
            >
              <tab.icon className="w-5 h-5" />
              <span className="text-xs font-semibold uppercase tracking-wider">{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="p-6 md:p-10">
          <form onSubmit={handleSearch} className="flex flex-col gap-6">
            {activeTab === 'text' && (
              <div className="relative">
                <input
                  type="text"
                  placeholder="Enter medicine name (e.g. Dolo 650)"
                  className="w-full pl-12 pr-6 py-4 rounded-2xl bg-slate-100 border-none focus:ring-2 focus:ring-medic-500 focus:bg-white transition-all text-lg"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-6 h-6" />
              </div>
            )}

            {(activeTab === 'prescription' || activeTab === 'tablet') && (
              <label className="border-2 border-dashed border-slate-200 rounded-3xl p-12 flex flex-col items-center gap-4 bg-slate-100/50 hover:bg-slate-100 transition-all cursor-pointer relative">
                <input
                  type="file"
                  accept="image/png, image/jpeg"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="p-4 bg-white rounded-full shadow-sm relative z-10">
                  {activeTab === 'prescription' ? <FileText className="text-medic-500 w-8 h-8" /> : <Camera className="text-medic-500 w-8 h-8" />}
                </div>
                <div className="text-center relative z-10">
                  <p className="text-slate-700 font-semibold text-lg">
                    {file ? file.name : `Click to upload ${activeTab === 'prescription' ? 'prescription' : 'photo'}`}
                  </p>
                  <p className="text-slate-400 text-sm">Max file size 5MB (JPG, PNG)</p>
                </div>
              </label>
            )}

            {activeTab === 'symptoms' && (
              <div className="relative">
                <textarea
                  placeholder="Describe how you're feeling... (e.g. fever, headache, body pain)"
                  className="w-full pl-6 pr-6 py-4 rounded-3xl bg-slate-100 border-none focus:ring-2 focus:ring-medic-500 focus:bg-white transition-all text-lg min-h-[120px]"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                ></textarea>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="gradient-bg text-white py-4 rounded-2xl font-bold text-lg shadow-lg hover:shadow-medic-200/50 hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                'Identify & Locate'
              )}
            </button>
          </form>
        </div>
      </main>

      {/* Results Section */}
      {results && (
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Medicine Info */}
          <section className="md:col-span-2 flex flex-col gap-6">
            <div className="bg-white rounded-3xl shadow-lg p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-slate-800 mb-1">{results.name}</h2>
                  <p className="text-medic-600 font-medium">{results.composition}</p>
                </div>
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm font-bold uppercase tracking-wider">
                  Available
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="flex gap-4">
                  <div className="p-3 bg-blue-50 rounded-xl h-fit">
                    <Info className="text-blue-500 w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-700 text-sm uppercase mb-1">Uses</h3>
                    <p className="text-slate-600 text-sm leading-relaxed">{results.uses}</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="p-3 bg-orange-50 rounded-xl h-fit">
                    <AlertCircle className="text-orange-500 w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-700 text-sm uppercase mb-1">Side Effects</h3>
                    <p className="text-slate-600 text-sm leading-relaxed">{results.sideEffects}</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-orange-50 border border-orange-100 rounded-2xl flex items-center gap-3 text-orange-700 text-sm">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <p><strong>Safety Notice:</strong> Consult with a doctor before taking any medication.</p>
              </div>
            </div>

            {/* Substitutes */}
            <div className="bg-white rounded-3xl shadow-lg p-8">
              <h3 className="text-lg font-bold text-slate-800 mb-4">Recommended Substitutes</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {results.substitutes.map(sub => (
                  <div key={sub} className="p-4 border border-slate-100 rounded-2xl bg-slate-50/50 hover:bg-slate-50 cursor-pointer transition-all flex justify-between items-center group">
                    <span className="font-semibold text-slate-700">{sub}</span>
                    <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-medic-500 transition-all" />
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Pharmacies Side Panel */}
          <section className="flex flex-col gap-6">
            <div className="bg-white rounded-3xl shadow-lg p-6 flex flex-col gap-4">
              <div className="flex items-center gap-2 mb-2">
                <MapPin className="text-medic-500 w-5 h-5" />
                <h3 className="font-bold text-slate-800">Nearby Availability</h3>
              </div>

              <div className="flex flex-col gap-3">
                {pharmacies.map((pharmacy, i) => (
                  <div key={i} className="p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-medic-200 transition-all">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-bold text-slate-800 text-sm">{pharmacy.name}</h4>
                      <span className="text-medic-600 font-bold text-xs">{pharmacy.distance}</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-500 text-xs mb-3">
                      <Clock className="w-3 h-3" />
                      <span>Open until 10 PM</span>
                    </div>
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${pharmacy.lat},${pharmacy.lon}`}
                      target="_blank"
                      rel="noreferrer"
                      className="w-full py-2 bg-white border border-slate-200 rounded-xl text-slate-700 text-xs font-bold hover:bg-medic-50 hover:border-medic-200 hover:text-medic-600 transition-all flex items-center justify-center gap-2"
                    >
                      Get Directions <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-3xl shadow-lg p-2 h-64 overflow-hidden">
              <MapComponent pharmacies={pharmacies} userLocation={userLocation} />
            </div>
          </section>
        </div>
      )}
    </div>
  );
};

export default App;
