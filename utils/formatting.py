"""
Formatting Utilities - Functions for formatting HTML output
"""
import json


def get_accuracy_badge(accuracy):
    """Return a colored badge based on accuracy percentage"""
    try:
        acc = int(accuracy)
        if acc >= 80:
            return f'<span class="badge bg-success ms-2">{acc}%</span>'
        elif acc >= 65:
            return f'<span class="badge bg-warning text-dark ms-2">{acc}%</span>'
        else:
            return f'<span class="badge bg-secondary ms-2">{acc}%</span>'
    except Exception:
        return ''


def format_characteristics_html(data):
    """Format the physical characteristics data as HTML for better display"""
    try:
        html = ""

        # Add header section
        html += f"""
        <div class="characteristic-header mb-4">
            <h4>Potential Physical Characteristics</h4>
            <div class="d-flex mb-3">
                <div class="badge bg-info me-2 p-2">Gender: {data.get('gender', 'Unknown')}</div>
                <div class="badge bg-info me-2 p-2">Ancestry: {data.get('ancestry', 'Unknown')}</div>
                <div class="badge bg-info p-2">Code: {data.get('population_code', 'Unknown')}</div>
            </div>
        </div>
        """

        # Get physical characteristics
        phys = data.get("physical_characteristics", {})
        if not phys:
            return f"""
            <div class="alert alert-warning">
                <h5><i class="fas fa-exclamation-triangle me-2"></i>Incomplete Data</h5>
                <p>No physical characteristics data found. Here is the raw data received:</p>
                <pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
            </div>
            """

        # Start the characteristics grid
        html += '<div class="row">'

        # Hair
        html += """
        <div class="col-md-6 col-lg-4 mb-3 fade-in-up" style="animation-delay: 0.1s">
            <div class="card physical-traits-card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-cut me-2"></i>Hair</h5>
                </div>
                <div class="card-body">
        """

        try:
            hair = phys.get("hair", {})
            color = hair.get("color", "Unknown")
            color_acc = hair.get("color_accuracy", "")
            texture = hair.get("texture", "Unknown")
            texture_acc = hair.get("texture_accuracy", "")
            
            # Handle if still array (backwards compatibility)
            if isinstance(color, list):
                color = color[0] if color else "Unknown"
            if isinstance(texture, list):
                texture = texture[0] if texture else "Unknown"
            
            html += f'<p><strong>Color:</strong> {color}{get_accuracy_badge(color_acc)}</p>'
            html += f'<p><strong>Texture:</strong> {texture}{get_accuracy_badge(texture_acc)}</p>'
        except Exception as e:
            html += f'<p class="text-danger">Error displaying hair data: {str(e)}</p>'

        html += "</div></div></div>"

        # Eyes
        html += """
        <div class="col-md-6 col-lg-4 mb-3 fade-in-up" style="animation-delay: 0.2s">
            <div class="card physical-traits-card">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0"><i class="fas fa-eye me-2"></i>Eyes</h5>
                </div>
                <div class="card-body">
        """

        try:
            eyes = phys.get("eyes", {})
            color = eyes.get("color", "Unknown")
            color_acc = eyes.get("color_accuracy", "")
            shape = eyes.get("shape", "Unknown")
            shape_acc = eyes.get("shape_accuracy", "")
            
            # Handle if still array
            if isinstance(color, list):
                color = color[0] if color else "Unknown"
            if isinstance(shape, list):
                shape = shape[0] if shape else "Unknown"
            
            html += f'<p><strong>Color:</strong> {color}{get_accuracy_badge(color_acc)}</p>'
            html += f'<p><strong>Shape:</strong> {shape}{get_accuracy_badge(shape_acc)}</p>'
        except Exception as e:
            html += f'<p class="text-danger">Error displaying eye data: {str(e)}</p>'

        html += "</div></div></div>"

        # Skin
        html += """
        <div class="col-md-6 col-lg-4 mb-3 fade-in-up" style="animation-delay: 0.3s">
            <div class="card physical-traits-card">
                <div class="card-header bg-warning text-dark">
                    <h5 class="mb-0"><i class="fas fa-palette me-2"></i>Skin</h5>
                </div>
                <div class="card-body">
        """

        try:
            skin = phys.get("skin", {})
            tone = skin.get("tone", "Unknown")
            tone_acc = skin.get("tone_accuracy", "")
            
            # Handle if still array
            if isinstance(tone, list):
                tone = tone[0] if tone else "Unknown"
            
            html += f'<p><strong>Tone:</strong> {tone}{get_accuracy_badge(tone_acc)}</p>'
        except Exception as e:
            html += f'<p class="text-danger">Error displaying skin data: {str(e)}</p>'

        html += "</div></div></div>"

        # Facial Features
        html += """
        <div class="col-md-6 col-lg-4 mb-3 fade-in-up" style="animation-delay: 0.4s">
            <div class="card physical-traits-card">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-user me-2"></i>Facial Features</h5>
                </div>
                <div class="card-body">
        """

        try:
            face = phys.get("facial_features", {})
            face_items = [
                ("nose", "nose_accuracy", "Nose"),
                ("lips", "lips_accuracy", "Lips"),
                ("face_shape", "face_shape_accuracy", "Face Shape"),
                ("chin", "chin_accuracy", "Chin"),
                ("cheekbones", "cheekbones_accuracy", "Cheekbones"),
            ]

            for key, acc_key, label in face_items:
                value = face.get(key, "")
                accuracy = face.get(acc_key, "")
                if value:
                    # Handle if still array
                    if isinstance(value, list):
                        value = value[0] if value else ""
                    if value:
                        html += f'<p><strong>{label}:</strong> {value}{get_accuracy_badge(accuracy)}</p>'
        except Exception as e:
            html += f'<p class="text-danger">Error displaying facial features: {str(e)}</p>'

        html += "</div></div></div>"

        # Body Structure
        html += """
        <div class="col-md-6 col-lg-4 mb-3 fade-in-up" style="animation-delay: 0.5s">
            <div class="card physical-traits-card">
                <div class="card-header bg-secondary text-white">
                    <h5 class="mb-0"><i class="fas fa-child me-2"></i>Body Structure</h5>
                </div>
                <div class="card-body">
        """

        try:
            body = phys.get("body_structure", {})
            body_items = [
                ("height", "height_accuracy", "Height"),
                ("build", "build_accuracy", "Build"),
                ("frame", "frame_accuracy", "Frame"),
            ]

            for key, acc_key, label in body_items:
                value = body.get(key, "")
                accuracy = body.get(acc_key, "")
                if value:
                    # Handle if still array
                    if isinstance(value, list):
                        value = value[0] if value else ""
                    if value:
                        html += f'<p><strong>{label}:</strong> {value}{get_accuracy_badge(accuracy)}</p>'
        except Exception as e:
            html += f'<p class="text-danger">Error displaying body structure: {str(e)}</p>'

        html += "</div></div></div>"

        # Other Traits
        html += """
        <div class="col-md-6 col-lg-4 mb-3 fade-in-up" style="animation-delay: 0.6s">
            <div class="card physical-traits-card">
                <div class="card-header bg-dark text-white">
                    <h5 class="mb-0"><i class="fas fa-fingerprint me-2"></i>Other Traits</h5>
                </div>
                <div class="card-body">
        """

        try:
            other_traits = phys.get("other_traits", {})
            if other_traits:
                if isinstance(other_traits, dict):
                    # New format with accuracy
                    for key, value in other_traits.items():
                        if not key.endswith('_accuracy') and value:
                            acc_key = f"{key}_accuracy"
                            accuracy = other_traits.get(acc_key, "")
                            html += f'<p>{value}{get_accuracy_badge(accuracy)}</p>'
                elif isinstance(other_traits, list):
                    # Old format - just list
                    for trait in other_traits[:2]:  # Limit to 2 traits
                        html += f"<p>{str(trait)}</p>"
                else:
                    html += f"<p>{str(other_traits)}</p>"
            else:
                html += "<p>No additional traits specified</p>"
        except Exception as e:
            html += f'<p class="text-danger">Error displaying other traits: {str(e)}</p>'

        html += "</div></div></div>"

        # Close the row
        html += "</div>"

        return html
    except Exception as e:
        # Return an error display if something goes wrong with the formatting
        return f"""
        <div class="alert alert-danger">
            <h5><i class="fas fa-exclamation-triangle me-2"></i>Error Processing Data</h5>
            <p>An error occurred while processing the data: {str(e)}</p>
            <div class="mt-3">
                <strong>Raw Data:</strong>
                <pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
            </div>
        </div>
        """


def format_disease_report_html(data):
    """Format the disease risk data as HTML for better display"""
    try:
        html = ""

        # Add header section
        html += f"""
        <div class="disease-report-header mb-4">
            <h4>Genetic Disease Risk Assessment</h4>
            <div class="d-flex mb-3">
                <div class="badge bg-info me-2 p-2">Gender: {data.get('profile_summary', {}).get('gender', 'Unknown')}</div>
                <div class="badge bg-info me-2 p-2">Ancestry: {data.get('profile_summary', {}).get('ancestry', 'Unknown')}</div>
                <div class="badge bg-info p-2">Code: {data.get('profile_summary', {}).get('population_code', 'Unknown')}</div>
            </div>
        </div>
        """

        # Add disease risks section
        disease_risks = data.get("disease_risks", [])
        if not disease_risks:
            html += """
            <div class="alert alert-info">
                <h5><i class="fas fa-info-circle me-2"></i>No Disease Risk Data</h5>
                <p>No specific disease risk information could be generated for this genetic profile.</p>
            </div>
            """
        else:
            html += '<div class="disease-risks-container">'

            # Loop through each disease
            for i, disease in enumerate(disease_risks):
                # Determine color based on risk level
                risk_level = disease.get("risk_level", "").lower()
                if "high" in risk_level:
                    risk_class = "bg-danger"
                elif "moderate" in risk_level:
                    risk_class = "bg-warning text-dark"
                else:
                    risk_class = "bg-success"

                # Create disease card
                html += f"""
                <div class="card disease-card mb-4 fade-in-up" style="animation-delay: {i * 0.1}s">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">{disease.get('disease_name', 'Unknown Disease')}</h5>
                        <span class="badge {risk_class} risk-badge">{disease.get('risk_level', 'Unknown Risk')}</span>
                    </div>
                    <div class="card-body">
                        <p><strong>Description:</strong> {disease.get('description', 'No description available')}</p>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Affected Genes:</strong> {', '.join(disease.get('affected_genes', ['Unknown']))}</p>
                                <p><strong>Prevalence:</strong> {disease.get('prevalence_in_population', 'Unknown prevalence')}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Key Mutations:</strong> {', '.join(disease.get('key_mutations', ['Not specified']))}</p>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <h6><i class="fas fa-clipboard-list me-2"></i>Recommendations:</h6>
                            <ul class="recommendations-list">
                """

                # Add recommendations
                recommendations = disease.get("recommendations", [])
                if recommendations:
                    for rec in recommendations:
                        html += f"<li>{rec}</li>"
                else:
                    html += "<li>No specific recommendations available</li>"

                html += """
                            </ul>
                        </div>
                    </div>
                </div>
                """

            html += "</div>"

        return html
    except Exception as e:
        # Return an error display if something goes wrong with the formatting
        return f"""
        <div class="alert alert-danger">
            <h5><i class="fas fa-exclamation-triangle me-2"></i>Error Processing Disease Data</h5>
            <p>An error occurred while processing the disease risk data: {str(e)}</p>
            <div class="mt-3">
                <strong>Raw Data:</strong>
                <pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
            </div>
        </div>
        """
