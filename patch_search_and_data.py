import json

with open('public/cropland_parcels.json', 'r', encoding='utf-8') as f:
    parcels_json = f.read()

with open('public/report.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace CROPLAND_PARCELS
start_marker = 'window.CROPLAND_PARCELS = '
end_marker = ';\n\n    const satelliteLayer'
idx_start = html.find(start_marker)
idx_end = html.find(end_marker)

if idx_start != -1 and idx_end != -1:
    html = html[:idx_start + len(start_marker)] + parcels_json.strip() + html[idx_end:]
    print('1. Successfully updated window.CROPLAND_PARCELS in HTML')
else:
    print('Failed to find CROPLAND_PARCELS markers:', idx_start, idx_end)

# 2. Make search container visible on all screens
html = html.replace('hidden sm:block', '')

# 3. Replace handleTopSearchInput
old_search_start = 'window.handleTopSearchInput = function(query) {'
old_search_end = 'window.onSelectSearchedParcel = function(parcelId) {'
s_start = html.find(old_search_start)
s_end = html.find(old_search_end)

new_search_code = '''window.handleTopSearchInput = function(query) {
      const dropdown = document.getElementById('searchSuggestionsDropdown');
      const clearBtn = document.getElementById('clearSearchBtn');
      if (!dropdown) return;

      const rawQ = (query || '').trim();
      const q = rawQ.toLowerCase();
      const qClean = q.replace(/[^a-z0-9]/g, '');
      if (clearBtn) clearBtn.className = q ? 'absolute right-2.5 text-slate-400 hover:text-slate-600 text-[16px]' : 'hidden';

      if (!q) {
        dropdown.innerHTML = `
          <div class="px-3 py-1.5 text-[10px] font-label-caps text-slate-400 uppercase tracking-wider bg-slate-50">Select Cropland Parcel (${window.CROPLAND_PARCELS.length} Available)</div>
          ${window.CROPLAND_PARCELS.map(p => `
            <div onclick="window.onSelectSearchedParcel('${p.id}')" class="px-3 py-2 hover:bg-slate-50 cursor-pointer flex items-center justify-between transition-colors border-b border-slate-100/60 last:border-b-0">
              <div>
                <div class="font-semibold text-xs text-slate-900">${p.name} <span class="text-[10px] text-slate-400 font-normal">#${p.survey_no || p.id}</span></div>
                <div class="text-[11px] text-slate-500">${p.area_acres} · ${p.timestamp}</div>
              </div>
              <span class="font-label-mono-num text-[11px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">NDVI ${(p.ndvi != null ? p.ndvi.toFixed(2) : '0.75')}</span>
            </div>
          `).join('')}
        `;
        dropdown.classList.remove('hidden');
        return;
      }

      const matches = window.CROPLAND_PARCELS.filter(p => {
        const nameLower = (p.name || '').toLowerCase();
        const idLower = (p.id || '').toLowerCase();
        const surveyLower = (p.survey_no || '').toLowerCase();
        const areaLower = (p.area_acres || '').toLowerCase();
        const timeLower = (p.timestamp || '').toLowerCase();

        const nameClean = nameLower.replace(/[^a-z0-9]/g, '');
        const idClean = idLower.replace(/[^a-z0-9]/g, '');
        const surveyClean = surveyLower.replace(/[^a-z0-9]/g, '');

        if (nameLower.includes(q) || idLower.includes(q) || surveyLower.includes(q) || areaLower.includes(q) || timeLower.includes(q)) return true;
        if (qClean && (nameClean.includes(qClean) || idClean.includes(qClean) || surveyClean.includes(qClean))) return true;

        if (p.aliases && p.aliases.some(a => {
          const aLower = a.toLowerCase();
          const aClean = aLower.replace(/[^a-z0-9]/g, '');
          return aLower.includes(q) || (qClean && aClean.includes(qClean));
        })) return true;

        return false;
      });

      if (matches.length === 0) {
        dropdown.innerHTML = `<div class="px-3 py-3 text-xs text-slate-500 text-center">No cropland found matching "<strong>${rawQ}</strong>"</div>`;
      } else {
        dropdown.innerHTML = `
          <div class="px-3 py-1.5 text-[10px] font-label-caps text-slate-400 uppercase tracking-wider bg-slate-50">${matches.length} Farmland Match${matches.length > 1 ? 'es' : ''}</div>
          ${matches.map(p => `
            <div onclick="window.onSelectSearchedParcel('${p.id}')" class="px-3 py-2 hover:bg-slate-50 cursor-pointer flex items-center justify-between transition-colors border-b border-slate-100/60 last:border-b-0">
              <div>
                <div class="font-semibold text-xs text-slate-900">${p.name} <span class="text-[10px] text-slate-400 font-normal">#${p.survey_no || p.id}</span></div>
                <div class="text-[11px] text-slate-500">${p.area_acres} · ${p.timestamp}</div>
              </div>
              <span class="font-label-mono-num text-[11px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">NDVI ${(p.ndvi != null ? p.ndvi.toFixed(2) : '0.75')}</span>
            </div>
          `).join('')}
        `;
      }
      dropdown.classList.remove('hidden');
    };

    '''

if s_start != -1 and s_end != -1:
    html = html[:s_start] + new_search_code + html[s_end:]
    print('2. Successfully updated handleTopSearchInput')
else:
    print('Failed to find search handler markers:', s_start, s_end)

with open('public/report.html', 'w', encoding='utf-8') as f:
    f.write(html)
with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
with open('dist/report.html', 'w', encoding='utf-8') as f:
    f.write(html)
with open('dist/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('3. Successfully synchronized report.html and index.html across public/ and dist/')
