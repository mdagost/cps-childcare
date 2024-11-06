let schoolsData = [];
let map;
let markers = [];

// Initialize the map
function initMap() {
    map = L.map('map').setView([41.8781, -87.6298], 11); // Centered on Chicago
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

// Fetch and process CSV data
async function fetchData() {
    try {
        const response = await fetch('https://raw.githubusercontent.com/mdagost/cps-childcare/refs/heads/main/data/final_childcare_dataset.csv');
        const text = await response.text();
        
        // Use Papa Parse to parse CSV
        Papa.parse(text, {
            header: true,
            complete: function(results) {
                // Filter out rows where all values are empty
                schoolsData = results.data
                    .filter(row => Object.values(row).some(value => value && value.trim() !== ''))
                    .map(row => ({
                        ...row,
                        lat: parseFloat(row.lat),
                        lng: parseFloat(row.lon)
                    }));
                currentFilteredData = schoolsData;
                populateNeighborhoodFilter();
                renderTable(schoolsData);
                addMarkersToMap(schoolsData);
            },
            error: function(error) {
                console.error('Error parsing CSV:', error);
            }
        });
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Render table with data
function renderTable(data) {
    const tbody = document.querySelector('#schools-table tbody');
    tbody.innerHTML = data.map(row => {
        return `
        <tr>
            <td>${row['Elementary School']}</td>
            <td>${row['Address']}</td>
            <td>${row['Neighborhood']}</td>
            <td style="color: green; text-align: center">${row['Provides Before Care'] === 'True' ? '✓' : ''}</td>
            <td style="color: green; text-align: center">${row['Provides After Care'] === 'True' ? '✓' : ''}</td>
            <td>${row['Before Care Start Time']}</td>
            <td>${row['Before Care Provider']}</td>
            <td data-sources>${row['Before Care Info'] || ''}</td>
            <td>${row['After Care End Time']}</td>
            <td>${row['After Care Provider']}</td>
            <td data-sources>${row['After Care Info'] || ''}</td>
            <td>${row['School Hours']}</td>
            <td>${row['Earliest Drop Off Time']}</td>
            <td>${row['After School Hours']}</td>
            <td>${row['Grades']}</td>
            <td>${row['Phone']}</td>
            <td>${row['Website'] ? `<a href="${row['Website']}" target="_blank">Website</a>` : ''}</td>
            <td>${row['Contact Page'] ? `<a href="${row['Contact Page']}" target="_blank">Contact</a>` : ''}</td>
        </tr>
    `}).join('');
}

// Add this helper function to scroll to a specific school row
function scrollToSchool(schoolName) {
    const tbody = document.querySelector('#schools-table tbody');
    const rows = tbody.getElementsByTagName('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const schoolCell = rows[i].cells[0];  // First cell contains school name
        if (schoolCell.textContent === schoolName) {
            rows[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
            rows[i].style.backgroundColor = '#fff3cd';  // Highlight the row
            setTimeout(() => {
                rows[i].style.backgroundColor = '';  // Remove highlight after 2 seconds
            }, 2000);
            break;
        }
    }
}

// Update the addMarkersToMap function
function addMarkersToMap(data) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    // Create a smaller icon
    const smallIcon = new L.Icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        iconSize: [15, 24],
        iconAnchor: [7, 24],
        popupAnchor: [1, -24],
    });

    // Add new markers
    data.forEach(school => {
        if (school.lat && school.lng) { // Only add marker if coordinates exist
            const marker = L.marker([school.lat, school.lng], { icon: smallIcon })
                .bindPopup(`
                    <b>${school['Elementary School']}</b><br>
                    ${school['Address']}<br>
                    Neighborhood: ${school['Neighborhood']}<br>
                    Hours: ${school['School Hours']}<br>
                    ${school['Provides Before Care'] === 'True' ? 
                        `Before Care: ${school['Before Care Start Time']} (${school['Before Care Provider']})<br>` : 
                        'No Before Care<br>'}
                    ${school['Provides After Care'] === 'True' ? 
                        `After Care: Until ${school['After Care End Time']} (${school['After Care Provider']})<br>` : 
                        'No After Care<br>'}
                    Grades: ${school['Grades']}<br>
                    ${school['Phone'] ? `Phone: ${school['Phone']}<br>` : ''}
                    ${school['Website'] ? `<a href="${school['Website']}" target="_blank">Website</a>` : ''}
                `);
            
            // Add click handler to scroll to the school's row
            marker.on('click', () => {
                scrollToSchool(school['Elementary School']);
            });
            
            markers.push(marker);
            marker.addTo(map);
        }
    });
}

// Search functionality
let currentSearchTerm = '';
let currentNeighborhood = '';
let currentBeforeCare = '';
let currentAfterCare = '';

// Keep track of current filtered data
let currentFilteredData = [];

function filterData() {
    const filtered = schoolsData.filter(school => {
        const searchFields = [
            school['Elementary School'] || '',
            school['Address'] || '',
            school['Neighborhood'] || ''
        ].map(field => field.toLowerCase());

        const matchesSearch = !currentSearchTerm || 
            searchFields.some(field => field.includes(currentSearchTerm.toLowerCase()));
            
        const matchesNeighborhood = !currentNeighborhood || 
            school['Neighborhood'] === currentNeighborhood;

        const matchesBeforeCare = !currentBeforeCare || 
            school['Provides Before Care'] === currentBeforeCare;

        const matchesAfterCare = !currentAfterCare || 
            school['Provides After Care'] === currentAfterCare;
            
        return matchesSearch && matchesNeighborhood && matchesBeforeCare && matchesAfterCare;
    });
    
    currentFilteredData = filtered;
    renderTable(filtered);
    addMarkersToMap(filtered);
}

// Sorting functionality
function sortData(data, column, direction) {
    const columnMap = {
        'school': 'Elementary School',
        'address': 'Address',
        'neighborhood': 'Neighborhood',
        'schoolHours': 'School Hours',
        'earliestDropOff': 'Earliest Drop Off Time',
        'afterSchoolHours': 'After School Hours',
        'grades': 'Grades',
        'phone': 'Phone',
        'website': 'Website',
        'contactPage': 'Contact Page',
        'beforeCare': 'Provides Before Care',
        'afterCare': 'Provides After Care',
        'beforeCareStart': 'Before Care Start Time',
        'beforeCareProvider': 'Before Care Provider',
        'beforeCareInfo': 'Before Care Info',
        'afterCareEnd': 'After Care End Time',
        'afterCareProvider': 'After Care Provider',
        'afterCareInfo': 'After Care Info'
    };

    const actualColumn = columnMap[column] || column;
    
    const sorted = [...data].sort((a, b) => {
        if (column === 'lat' || column === 'lng') {
            return direction === 'asc' ? a[column] - b[column] : b[column] - a[column];
        }
        
        const valA = String(a[actualColumn] || '');
        const valB = String(b[actualColumn] || '');
        
        return direction === 'asc' 
            ? valA.localeCompare(valB)
            : valB.localeCompare(valA);
    });
    return sorted;
}

// Add this function to populate the neighborhood dropdown
function populateNeighborhoodFilter() {
    const neighborhoods = [...new Set(schoolsData.map(school => school['Neighborhood']))].sort();
    const select = document.getElementById('filter-region');
    select.innerHTML = '<option value="">Filter by neighborhood...</option>' +
        neighborhoods.map(neighborhood => 
            `<option value="${neighborhood}">${neighborhood}</option>`
        ).join('');
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    fetchData();

    // Search input
    document.getElementById('search').addEventListener('input', (e) => {
        currentSearchTerm = e.target.value;
        filterData();
    });

    // Neighborhood filter
    document.getElementById('filter-region').addEventListener('change', (e) => {
        currentNeighborhood = e.target.value;
        filterData();
    });

    // Before Care filter
    document.getElementById('filter-before-care').addEventListener('change', (e) => {
        currentBeforeCare = e.target.value;
        filterData();
    });

    // After Care filter
    document.getElementById('filter-after-care').addEventListener('change', (e) => {
        currentAfterCare = e.target.value;
        filterData();
    });

    // Column sorting
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const column = th.dataset.sort;
            const currentDirection = th.dataset.direction || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            
            document.querySelectorAll('th').forEach(header => header.removeAttribute('data-direction'));
            th.dataset.direction = newDirection;

            const sorted = sortData(currentFilteredData, column, newDirection);
            renderTable(sorted);
            addMarkersToMap(sorted);
        });
    });
}); 