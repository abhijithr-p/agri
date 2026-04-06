/**
 * SMARTFARM 3D - PREMIUM AGRICULTURE INTELLIGENCE
 * Advanced 3D Canvas, API Integration, and Interactive Features
 */

// =====================================================
// 3D CANVAS INITIALIZATION - AGRICULTURAL THEME
// =====================================================

function initializeCanvas() {
    const canvas = document.getElementById('canvas3d');
    if (!canvas) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0xF5E6D3, 1);
    camera.position.z = 30;

    // Create animated starfield background
    const starsGeometry = new THREE.BufferGeometry();
    const starsMaterial = new THREE.PointsMaterial({
        color: 0xDCC5B0,
        size: 0.5,
        sizeAttenuation: true,
        transparent: true,
        opacity: 0.4
    });

    const starsVertices = [];
    for (let i = 0; i < 1000; i++) {
        const x = (Math.random() - 0.5) * 200;
        const y = (Math.random() - 0.5) * 200;
        const z = (Math.random() - 0.5) * 200;
        starsVertices.push(x, y, z);
    }

    starsGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(starsVertices), 3));
    const stars = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(stars);

    // Create animated agricultural fields
    const fields = [];
    for (let i = 0; i < 5; i++) {
        const fieldGeometry = new THREE.BoxGeometry(2, 0.5, 3);
        const fieldMaterial = new THREE.MeshPhongMaterial({
            color: 0x2D8B6F,
            emissive: 0x1E5F4D,
            shininess: 100
        });
        const field = new THREE.Mesh(fieldGeometry, fieldMaterial);
        field.position.set(i * 8 - 16, -5 - i * 0.5, -15);
        field.rotation.x = 0.3;
        field.scale.y = 0.3;
        scene.add(field);
        fields.push(field);
    }

    // Create particles for organic feel
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesMaterial = new THREE.PointsMaterial({
        color: 0x6ECCC4,
        size: 0.2,
        transparent: true,
        opacity: 0.3
    });

    const particlesVertices = [];
    for (let i = 0; i < 500; i++) {
        const x = (Math.random() - 0.5) * 100;
        const y = (Math.random() - 0.5) * 100;
        const z = (Math.random() - 0.5) * 100;
        particlesVertices.push(x, y, z);
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(particlesVertices), 3));
    const particles = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particles);

    // Professional lighting setup
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xE8956D, 0.5);
    directionalLight.position.set(10, 20, 10);
    scene.add(directionalLight);

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);

        // Slowly rotating stars
        stars.rotation.x += 0.0001;
        stars.rotation.y += 0.0002;

        // Animate particles
        particles.rotation.x += 0.0001;
        particles.rotation.y += 0.0003;

        // Animate fields with wave effect
        fields.forEach((field, index) => {
            field.rotation.y += 0.002;
            field.position.y += Math.sin(Date.now() * 0.0001 + index) * 0.0005;
        });

        renderer.render(scene, camera);
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    animate();
}

// Initialize 3D canvas when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCanvas);
} else {
    initializeCanvas();
}

// =====================================================
// API CONFIGURATION
// =====================================================

const BASE_URL = "http://localhost:8000";

// =====================================================
// REGISTRATION FORM LOGIC
// =====================================================

const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const errorMsg = document.getElementById("error-msg");
        errorMsg.textContent = "";

        const payload = {
            contact: document.getElementById("f-contact").value,
            password: document.getElementById("f-password").value,
            crop: document.getElementById("f-crop").value,
            soil: document.getElementById("f-soil").value,
            land: document.getElementById("f-land").value,
            area: String(document.getElementById("f-area").value || "0"),
            location: document.getElementById("f-location") ? document.getElementById("f-location").value : "Bangalore"
        };

        try {
            const response = await fetch(`${BASE_URL}/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                if (data.message === "Registered successfully") {
                    alert("✅ Registration successful! Redirecting to login...");
                    window.location.href = "login.html";
                } else {
                    errorMsg.textContent = data.message || "Registration failed.";
                }
            } else {
                errorMsg.textContent = data.detail || "Registration failed.";
            }

        } catch (error) {
            console.error("Network Error: ", error);
            errorMsg.textContent = "❌ Cannot connect to backend. Ensure the server is running.";
        }
    });
}

// =====================================================
// LOGIN FORM LOGIC
// =====================================================

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const errorMsg = document.getElementById("error-msg");
        errorMsg.textContent = "";

        const contact = document.getElementById("f-contact").value;
        const password = document.getElementById("f-password").value;

        try {
            const response = await fetch(`${BASE_URL}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ contact, password })
            });

            const data = await response.json();

            if (response.ok && data.crop) {
                localStorage.setItem("user", JSON.stringify(data));
                alert("✅ Login successful! Welcome back.");
                window.location.href = "dashboard.html";
            } else {
                errorMsg.textContent = data.detail || data.message || "Invalid credentials.";
            }

        } catch (error) {
            console.error("Network Error: ", error);
            errorMsg.textContent = "❌ Cannot connect to backend server.";
        }
    });
}

// =====================================================
// DASHBOARD PROTECTION & LOADING
// =====================================================

if (window.location.pathname.includes("dashboard.html")) {
    const userString = localStorage.getItem("user");
    if (!userString) {
        window.location.href = "login.html";
    } else {
        try {
            const user = JSON.parse(userString);
            if (!user || !user.crop) {
                window.location.href = "login.html";
            } else {
                loadDashboard(user.crop);
                loadSmartIrrigation(user.crop, user.location || "Bangalore");
            }
        } catch (e) {
            window.location.href = "login.html";
        }
    }
}

// =====================================================
// DASHBOARD STAGE FUNCTIONS
// =====================================================

function startStage(stageName) {
    alert(`🚀 Starting "${stageName}" stage!\n\nMonitor your crop carefully during this phase with real-time AI insights.`);
}

function loadDashboard(crop) {
    const stageCards = document.getElementById("stage-cards");
    if (!stageCards) return;

    const stages = {
        rice: [
            { name: "Land Preparation", desc: "🌍 Soil testing, field leveling, and nutrient enrichment" },
            { name: "Seedling", desc: "🌱 Nursery management, seed germination (30-40 days)" },
            { name: "Transplanting", desc: "🚜 Transplant seedlings into prepared main field" },
            { name: "Vegetative", desc: "🌿 Plant growth, tillering stage (45-60 days)" },
            { name: "Flowering", desc: "🌸 Panicle initiation and flowering (20-30 days)" },
            { name: "Harvesting", desc: "🌾 Grain maturation and mechanical harvesting" }
        ],
        wheat: [
            { name: "Field Preparation", desc: "🌍 Soil preparation and sowing (October-November)" },
            { name: "Germination", desc: "🌱 Seed sprouting and root development" },
            { name: "Tillering", desc: "🌿 Shoot multiplication stage (30-40 days)" },
            { name: "Booting", desc: "🌾 Spike emergence and stem elongation" },
            { name: "Flowering", desc: "🌸 Anthesis and pollination phase" },
            { name: "Maturation", desc: "🏆 Grain filling and harvesting (April-May)" }
        ],
        corn: [
            { name: "Soil Setup", desc: "🌍 Field preparation and soil amendment" },
            { name: "Planting", desc: "🌱 Sowing seeds at optimal depth (April-May)" },
            { name: "Growth", desc: "🌿 Vegetative stage and leaf development (45 days)" },
            { name: "Tasseling", desc: "🌾 Male flower emergence from top" },
            { name: "Silking", desc: "🌸 Female flower and pollination window" },
            { name: "Harvest", desc: "🏆 Grain maturity and mechanical harvest (August-September)" }
        ]
    };

    const cropStages = stages[crop] || stages.rice;
    stageCards.innerHTML = cropStages.map(stage => `
        <div class="stage-card">
            <h3>${stage.name}</h3>
            <p>${stage.desc}</p>
            <button class="btn btn-primary stage-btn" onclick="startStage('${stage.name}')">
                ▶️ Start This Stage
            </button>
        </div>
    `).join('');
}

function loadSmartIrrigation(crop, location) {
    const irrigationInfo = document.getElementById("irrigation-info");
    const irrigationCard = document.getElementById("irrigation-card");
    if (!irrigationInfo || !irrigationCard) return;

    const irrigationData = {
        rice: {
            water: "1200-1500 mm",
            frequency: "Every 7-10 days",
            method: "Flood irrigation with 5-10cm standing water"
        },
        wheat: {
            water: "400-600 mm",
            frequency: "Every 15-20 days",
            method: "Furrow or drip irrigation"
        },
        corn: {
            water: "500-800 mm",
            frequency: "Every 10-15 days",
            method: "Drip or center pivot irrigation"
        }
    };

    const data = irrigationData[crop] || irrigationData.rice;

    irrigationInfo.innerHTML = `
        <strong style="display: block;">💧 Water Requirement:</strong>
        <span>${data.water}</span><br>
        <strong style="display: block; margin-top: 0.5rem;">⏱️ Frequency:</strong>
        <span>${data.frequency}</span>
    `;

    irrigationCard.innerHTML = `
        <h3>💧 Smart Irrigation Analysis</h3>
        <div style="margin-top: 1.5rem; display: grid; gap: 1rem;">
            <div>
                <strong>Method:</strong><br>
                <p style="color: var(--text-secondary); margin-top: 0.3rem;">${data.method}</p>
            </div>
            <div>
                <strong>Total Water Needed:</strong><br>
                <p style="color: var(--primary); margin-top: 0.3rem; font-weight: bold;">${data.water}</p>
            </div>
            <div>
                <strong>Irrigation Schedule:</strong><br>
                <p style="color: var(--text-secondary); margin-top: 0.3rem;">${data.frequency}</p>
            </div>
            <div style="padding: 1rem; background: rgba(46, 204, 113, 0.1); border-radius: 8px; border-left: 3px solid var(--primary);">
                <span style="color: var(--primary); font-weight: bold;">✅ Optimized for ${location}</span>
            </div>
        </div>
    `;
}

// =====================================================
// DISEASE DETECTION & ANALYSIS
// =====================================================

const analyzeBtn = document.getElementById("analyze-btn");
const diseaseImg = document.getElementById("disease-img");
const diseaseResult = document.getElementById("disease-result");

if (analyzeBtn && diseaseImg) {
    analyzeBtn.addEventListener("click", async () => {
        const file = diseaseImg.files[0];
        if (!file) {
            alert("⚠️ Please select a leaf image to analyze.");
            return;
        }

        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "🔄 Analyzing...";

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(`${BASE_URL}/predict`, {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                diseaseResult.style.display = 'block';
                diseaseResult.innerHTML = `
                    <h4 style="color: var(--primary); margin-bottom: 1rem;">🔍 AI Analysis Results</h4>
                    <div style="display: grid; gap: 0.8rem;">
                        <div>
                            <strong>Status:</strong>
                            <p style="color: var(--text-secondary); margin-top: 0.2rem;">${data.prediction || "Healthy Crop"}</p>
                        </div>
                        <div>
                            <strong>Confidence Level:</strong>
                            <p style="color: var(--primary); font-weight: bold; margin-top: 0.2rem;">${(data.confidence * 100).toFixed(2)}%</p>
                        </div>
                        <div>
                            <strong>Recommendation:</strong>
                            <p style="color: var(--text-secondary); margin-top: 0.2rem;">${data.recommendation || "No specific treatment needed. Continue monitoring."}</p>
                        </div>
                    </div>
                `;
            } else {
                diseaseResult.style.display = 'block';
                diseaseResult.innerHTML = `<p style="color: #ff6b6b; font-weight: bold;">⚠️ Analysis Error: ${data.detail || "Unable to process image"}</p>`;
            }
        } catch (error) {
            console.error("Error:", error);
            diseaseResult.style.display = 'block';
            diseaseResult.innerHTML = `<p style="color: #ff6b6b; font-weight: bold;">❌ Connection Error. Please try again.</p>`;
        }

        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "🔬 Analyze Leaf";
    });
}

// =====================================================
// LOGOUT FUNCTIONALITY
// =====================================================

const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        if (confirm("👋 Are you sure you want to logout?")) {
            localStorage.removeItem("user");
            alert("Logged out successfully!");
            window.location.href = "index.html";
        }
    });
}

// =====================================================
// SMOOTH SCROLLING BEHAVIOR
// =====================================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// =====================================================
// SCROLL ANIMATION WITH INTERSECTION OBSERVER
// =====================================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Apply observer to feature and stage cards
document.querySelectorAll('.feature-card, .stage-card, .about-card').forEach(card => {
    observer.observe(card);
});

// =====================================================
// MARKETPLACE PROTECTION
// =====================================================

if (window.location.pathname.includes("marketplace.html")) {
    if (!localStorage.getItem("user")) {
        window.location.href = "login.html";
    }
}