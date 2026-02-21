import win32com.client
import pythoncom
import sys
import os

def connect_to_sw():
    try:
        # Try specific version progID if generic fails, e.g. "SldWorks.Application.31" (2023)
        # But generic usually works.
        sw = win32com.client.GetActiveObject("SldWorks.Application")
        # Ensure we get the dynamic object to allow late binding which is more flexible
        sw = win32com.client.dynamic.Dispatch(sw)
        return sw
    except:
        try:
            sw = win32com.client.Dispatch("SldWorks.Application")
            sw.Visible = True
            return sw
        except:
            print("Could not connect to SolidWorks.")
            return None

def generate_part():
    swApp = connect_to_sw()
    if not swApp:
        return

    # Constants from OCR
    TOTAL_LENGTH = 205.0
    WIDTH = 32.0
    ARCH_OUTER_R = 73.0
    ARCH_INNER_R = 55.0
    HOLE_CENTER_DIST = 146.0
    HOLE_DIA = 14.0
    FOOT_THICKNESS = 22.0  # From "Left vertical thickness dimension: 22"
    
    # 1. Get Active Document (Assuming user created a new part manually)
    model = swApp.ActiveDoc
    
    if not model:
        print("No active document found. Please open a new Part file in SolidWorks manually before running this script.")
        # Try to create one last time as fallback, but don't crash if fails
        try:
             model = swApp.NewDocument("C:\\ProgramData\\SolidWorks\\SolidWorks 2023\\templates\\Part.prtdot", 0, 0, 0)
        except:
             pass
    
    if not model:
        print("Error: Could not access active document.")
        return

    # Set Title (Optional, might fail if not saved)
    # model.SetTitle2("Generated_Bracket")
    
    # 2. Create Main Profile (Front Plane)
    # Select Front Plane
    # SelectByID2 arguments: Name, Type, X, Y, Z, Append, Mark, Callout, SelectOption
    # Type mismatch often happens with the 'Callout' (None) or 'Mark' (0) arguments in pythoncom
    # Trying with Nothing for Callout (using None is usually correct, but let's try wrapping)
    
    # Try selecting by name simply first if possible, or correct args
    try:
        # Note: In some SW API versions, "Front Plane" might be localized (e.g. "前视基准面" in Chinese)
        # We should try English first, then localized if needed, or get by index.
        # But here the error is Type Mismatch, likely int vs long or similar in COM.
        
        # win32com often needs explicit types. 
        # SelectByID2(Name, Type, X, Y, Z, Append, Mark, Callout, SelectOption)
        # X, Y, Z are doubles. Append is bool. Mark is int. Callout is Dispatch. SelectOption is int.
        
        # Try a safer selection method: GetFeatureByName
        feature = model.FeatureByName("Front Plane")
        if not feature:
             feature = model.FeatureByName("前视基准面") # Try Chinese name
        
        if feature:
            feature.Select2(False, 0)
        else:
            # Fallback to SelectByID2 with safer args
            model.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, None, 0)
            
    except Exception as e:
        print(f"Selection failed: {e}")
        return

    model.SketchManager.InsertSketch(True)
    
    # Draw Profile
    # Center at (0,0)
    # Outer Arc
    # Note: SolidWorks API coordinates are in Meters
    scale = 0.001
    
    skManager = model.SketchManager
    
    # Base Line (Bottom)
    # From -102.5 to 102.5 (205 total)
    skManager.CreateLine(-TOTAL_LENGTH/2 * scale, 0, 0, TOTAL_LENGTH/2 * scale, 0, 0)
    
    # Vertical Lines (Feet sides)
    # Up to Foot Thickness
    skManager.CreateLine(-TOTAL_LENGTH/2 * scale, 0, 0, -TOTAL_LENGTH/2 * scale, FOOT_THICKNESS * scale, 0)
    skManager.CreateLine(TOTAL_LENGTH/2 * scale, 0, 0, TOTAL_LENGTH/2 * scale, FOOT_THICKNESS * scale, 0)
    
    # Top of Feet (Horizontal inwards)
    # We need to calculate where the arch starts.
    # Arch Outer R73. Center likely at (0,0) or (0, some_height).
    # Assuming semicircular arch resting on the feet? 
    # Or center is at y=0? If center is at y=0, R73 goes up to y=73.
    # Feet Top Lines
    # From (-102.5, 22) to (-73, 22)? 
    # Let's assume the arch starts at x = +/- 73.
    
    skManager.CreateLine(-TOTAL_LENGTH/2 * scale, FOOT_THICKNESS * scale, 0, -ARCH_OUTER_R * scale, FOOT_THICKNESS * scale, 0)
    skManager.CreateLine(TOTAL_LENGTH/2 * scale, FOOT_THICKNESS * scale, 0, ARCH_OUTER_R * scale, FOOT_THICKNESS * scale, 0)
    
    # Outer Arch
    # Center (0,0), Start (-73, 22), End (73, 22)? 
    # No, R73 implies x=73 at y=0. 
    # If thickness is 22, and R73 is outer radius. 
    # Let's approximate: Arc from (-73, 22) to (73, 22) with center (0,0)?
    # Actually, usually these brackets have the center of the arc at the bottom line (y=0).
    # So we draw an arc from (-73, 0) to (73, 0).
    # But we have feet.
    # Let's use the Trim/Convert entities approach or just draw the shape.
    
    # Alternative: Draw full Outer Arc, Draw full Inner Arc, Close bottom.
    # Outer Arc: Center(0,0), Radius 73.
    skManager.CreateArc(0, 0, 0, -ARCH_OUTER_R * scale, 0, 0, ARCH_OUTER_R * scale, 0, 0, 1) # Direction?
    
    # Inner Arc: Center(0,0), Radius 55.
    skManager.CreateArc(0, 0, 0, -ARCH_INNER_R * scale, 0, 0, ARCH_INNER_R * scale, 0, 0, 1)
    
    # Close the shape?
    # This is complex to guess exactly without seeing the lines.
    # Based on "Bracket", it's likely:
    # 1. Extrude the full "Arch" (R73 - R55).
    # 2. Extrude the "Feet" separately.
    
    # Let's try a simpler approach: 2 Features.
    model.SketchManager.InsertSketch(True) # Close sketch (cancel)
    
    # Feature 1: The Arch
    try:
        feature = model.FeatureByName("Front Plane")
        if not feature: feature = model.FeatureByName("前视基准面")
        if feature: feature.Select2(False, 0)
    except:
        pass
        
    model.SketchManager.InsertSketch(True)
    skManager.CreateArc(0, 0, 0, -ARCH_OUTER_R * scale, 0, 0, ARCH_OUTER_R * scale, 0, 0, 1) # Outer Semicircle
    skManager.CreateLine(-ARCH_OUTER_R * scale, 0, 0, -ARCH_INNER_R * scale, 0, 0) # Bottom left segment
    skManager.CreateArc(0, 0, 0, -ARCH_INNER_R * scale, 0, 0, ARCH_INNER_R * scale, 0, 0, 1) # Inner Semicircle
    skManager.CreateLine(ARCH_INNER_R * scale, 0, 0, ARCH_OUTER_R * scale, 0, 0) # Bottom right segment
    
    model.FeatureManager.FeatureExtrusion2(True, False, False, 0, 0, WIDTH * scale, 0.01, False, False, False, False, 0, 0, False, False, False, False, True, True, True, 0, 0, False)
    
    # Feature 2: The Feet
    # Sketch on the bottom face of the arch? Or Front Plane again.
    try:
        feature = model.FeatureByName("Front Plane")
        if not feature: feature = model.FeatureByName("前视基准面")
        if feature: feature.Select2(False, 0)
    except:
        pass
        
    model.SketchManager.InsertSketch(True)
    
    # Left Foot
    # Rect from (-102.5, 0) to (-73, 22) ? 
    # Let's assume foot height matches the start of the arc? 
    # If the arc is R73 centered at 0, at x=73 y=0.
    # So the feet must extend outwards from x=73 to x=102.5.
    # And have a height. 
    # OCR: "Left vertical thickness dimension: 22".
    # Let's assume height is 22.
    skManager.CreateCornerRectangle(-TOTAL_LENGTH/2 * scale, 0, 0, -ARCH_OUTER_R * scale, FOOT_THICKNESS * scale, 0)
    
    # Right Foot
    skManager.CreateCornerRectangle(ARCH_OUTER_R * scale, 0, 0, TOTAL_LENGTH/2 * scale, FOOT_THICKNESS * scale, 0)
    
    model.FeatureManager.FeatureExtrusion2(True, False, False, 0, 0, WIDTH * scale, 0.01, False, False, False, False, 0, 0, False, False, False, False, True, True, True, 0, 0, False)
    
    # Feature 3: Holes
    # Select Top Face of Left Foot
    # We need to select the face. A bit tricky by ID.
    # Let's sketch on Top Plane and Cut Extrude.
    try:
        feature = model.FeatureByName("Top Plane")
        if not feature: feature = model.FeatureByName("上视基准面")
        if feature: feature.Select2(False, 0)
    except:
        pass
        
    model.SketchManager.InsertSketch(True)
    
    # Left Hole
    skManager.CreateCircle(-HOLE_CENTER_DIST/2 * scale, WIDTH/2 * scale, 0, (-HOLE_CENTER_DIST/2 + HOLE_DIA/2) * scale, WIDTH/2 * scale, 0)
    
    # Right Hole
    skManager.CreateCircle(HOLE_CENTER_DIST/2 * scale, WIDTH/2 * scale, 0, (HOLE_CENTER_DIST/2 + HOLE_DIA/2) * scale, WIDTH/2 * scale, 0)
    
    # Cut Extrude
    # Through All
    model.FeatureManager.FeatureCut4(True, False, False, 1, 0, 0.1, 0.1, False, False, False, False, 0, 0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
    
    print("Part generation logic executed.")

if __name__ == "__main__":
    generate_part()
