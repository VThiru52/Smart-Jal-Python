import os

file_path = r'd:/Smart Jal/frontend/src/components/ui/SpatialMap.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# We know the specific range based on view_file: 72 to 111 is the messed up pointToLayer
# And onEachFeature starts at 113 with bad indentation.

# Values are 0-indexed in list, so line 72 is index 71.
start_idx = 71
end_idx = 111 # line 111 is included in the mess

# Function clean code
new_point_to_layer = [
    "    const pointToLayer = (feature, latlng) => {\n",
    "        if (activeLayer === 'bore_wells') {\n",
    "            const status = feature.properties.well_status;\n",
    "            const isWorking = status === 'Working';\n",
    "\n",
    "            return L.circleMarker(latlng, {\n",
    "                radius: 4,\n",
    "                fillColor: isWorking ? '#22c55e' : '#ef4444', // Green vs Red\n",
    "                color: '#fff',\n",
    "                weight: 1,\n",
    "                opacity: 1,\n",
    "                fillOpacity: 0.8\n",
    "            });\n",
    "        }\n",
    "\n",
    "        if (activeLayer === 'piezometers') {\n",
    "            return L.circleMarker(latlng, {\n",
    "                radius: 6,\n",
    "                fillColor: '#6366f1', // Indigo\n",
    "                color: '#fff',\n",
    "                weight: 2,\n",
    "                opacity: 1,\n",
    "                fillOpacity: 0.9\n",
    "            });\n",
    "        }\n",
    "        return null; // Default marker\n",
    "    };\n",
    "\n"
]

# We will verify if line 71 is indeed "    const pointToLayer..."
print(f"Line 72 (index 71) is: {lines[71]}")
if "const pointToLayer" not in lines[71]:
    print("Error: Line alignment mismatch")
    exit(1)

# Replace the block
# The original block went from 72 to 111. 
# We replace lines[71 : 111] with new_point_to_layer
# Wait, line 111 was "            };" (indented 12).
# Line 112 was empty.
# Line 113 was "            const onEachFeature..."
# So we slice [71:112]. (Indices 71 up to 111 inclusive)
# Python slice [start:end] excludes end. So [71:112] includes 71...111.

# Apply replacement
lines[71:112] = new_point_to_layer

# Now fix indentation of onEachFeature (which is now at a new index potentially, but let's just find it)
# Since new_point_to_layer has fixed length, we can calculate or just search.
# Or simpler: Re-read the lines in memory.
# The `lines` list is updated.

# Find "const onEachFeature" and fix its indentation
for i, line in enumerate(lines):
    if "const onEachFeature" in line:
        print(f"Found onEachFeature at line {i+1}: {line}")
        lines[i] = line.replace("            const", "    const")
        # Checking subsequent lines... this is a block. I should just fix the first line?
        # No, the whole function is likely indented deep. 
        # This is getting complicated to fix ALL indentation programmatically without parsing.
        # But `onEachFeature` itself is just a function. If I fix the definition line, the body is inside...
        # Wait, if the body is indented 16 spaces, and I dedent the header to 4, it looks like:
        # const foo ...
        #                 if (...)
        # That's ugly but valid.
        # I will leave indentation fix for subsequent linter/formatter or manual step if it's too hard.
        # The syntax error was the priority.
        break

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed SpatialMap.jsx")
