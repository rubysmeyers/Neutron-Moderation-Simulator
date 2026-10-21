import random
import math
import matplotlib.pyplot as plt 
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="Why CANDU Uses Heavy Water")
st.title("Why Bruce Power's Reactors Use Heavy Water")
st.caption("A neutron moderation simulator by Ruby Meyers")
st.markdown(
    "Fission makes **fast** neutrons, but a reactor needs **slow** ones to keep the chain reaction going. "
    "A **moderator** slows neutrons down by bouncing them off light atoms. "
    "This simulator fires thousands of virtual neutrons into three moderators to show why CANDU reactors, "
    "like the ones at Bruce Power, use heavy water and can run on natural uranium."
)

# ---------- Starting values ----------
start_energy = 2_000_000
thermal_energy = 0.025

# ---------- Controls in the sidebar ----------
st.sidebar.header("Controls")
number_of_neutrons = st.sidebar.slider("Neutrons per moderator", 1000, 10000, 3000, step=1000)
use_absorption = st.sidebar.checkbox("Include absorption", value=True)
heavy_water_ratio = st.sidebar.slider(
    "Heavy water purity (moderating ratio)", 1000, 12000, 12000, step=500,
    help="12,000 is pure heavy water. Lower values mimic light water leaking in.",
)

materials = {
    "Light water (H2O)": {"atoms": [(1, 40.0), (16, 3.8)], "moderating_ratio": 72},
    "Heavy water (D2O)": {"atoms": [(2, 6.8), (16, 3.8)], "moderating_ratio": heavy_water_ratio},
    "Graphite (C)": {"atoms": [(12, 4.7)], "moderating_ratio": 170},
}

# ---------- Physics functions (same as my Colab notebook) ----------
def collide(energy, mass):
    alpha = ((mass - 1) / (mass + 1)) ** 2
    return random.uniform(alpha * energy, energy)

def energy_history(mass):
    energy = start_energy
    history = [energy]
    while energy > thermal_energy:
        energy = collide(energy, mass)
        history.append(energy)
    return history

def pick_atom(atoms):
    masses = [mass for mass, chance in atoms]
    chances = [chance for mass, chance in atoms]
    return random.choices(masses, weights=chances)[0]

def xi(mass):
    if mass == 1:
        return 1.0
    alpha = ((mass - 1) / (mass + 1)) ** 2
    return 1 + alpha * math.log(alpha) / (1 - alpha)

def absorb_chance(material):
    if not use_absorption:
        return 0
    atoms = materials[material]["atoms"]
    total = sum(chance for mass, chance in atoms)
    material_xi = sum(chance * xi(mass) for mass, chance in atoms) / total
    return material_xi / materials[material]["moderating_ratio"]

def run_material(material, number_of_neutrons):
    atoms = materials[material]["atoms"]
    p_absorb = absorb_chance(material)
    survived = 0
    total_collisions = 0
    for i in range(number_of_neutrons):
        energy = start_energy
        collisions = 0
        absorbed = False
        while energy > thermal_energy:
            if random.random() < p_absorb:
                absorbed = True
                break
            energy = collide(energy, pick_atom(atoms))
            collisions = collisions + 1
        if not absorbed:
            survived = survived + 1
            total_collisions = total_collisions + collisions
    return survived / number_of_neutrons * 100, total_collisions / survived

# ---------- Section 1: one neutron ----------
st.header("1. Watch one neutron slow down")
st.write("Each dot is one collision. Press the button to fire new neutrons; every run is random.")
st.button("Fire new neutrons")

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(energy_history(1), marker="o", label="Hydrogen (light water)")
ax.plot(energy_history(2), marker="o", label="Deuterium (heavy water)")
ax.plot(energy_history(12), marker="o", label="Carbon (graphite)")
ax.set_yscale("log")
ax.axhline(thermal_energy, color="gray", linestyle="--", label="Thermal energy (0.025 eV)")
ax.set_xlabel("Collision number")
ax.set_ylabel("Neutron energy (eV)")
ax.set_title("One neutron slowing down in three moderators")
ax.legend()
st.pyplot(fig)

# ---------- Section 2: thousands of neutrons ----------
st.header("2. Run thousands of neutrons")
st.write("Change the controls in the sidebar to see how the results shift.")

results = []
with st.spinner("Simulating neutrons..."):
    for material in materials:
        percent, avg = run_material(material, number_of_neutrons)
        results.append({
            "Moderator": material,
            "Neutrons surviving (%)": round(percent, 1),
            "Average collisions": round(avg, 1),
        })
st.table(results)

fig2, ax2 = plt.subplots(figsize=(9, 4))
names = [row["Moderator"] for row in results]
survival = [row["Neutrons surviving (%)"] for row in results]
bars = ax2.bar(names, survival, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
ax2.bar_label(bars, fmt="%.1f%%")
ax2.set_ylim(0, 110)
ax2.set_ylabel("Neutrons surviving (%)")
ax2.set_title("How many neutrons survive slowing down?")
st.pyplot(fig2)

# ---------- Section 3: what it means ----------
st.header("3. What this shows")
st.markdown(
    "- **Light water** slows neutrons fastest, but hydrogen absorbs about 1 in 4 of them. "
    "Natural uranium is only about 0.7% U-235, so light-water reactors must use enriched fuel to make up for the loss.\n"
    "- **Heavy water** takes more bounces, but deuterium almost never absorbs a neutron. "
    "That is why CANDU reactors can run on natural uranium and skip enrichment.\n"
    "- **Graphite** works too, but needs over 100 bounces, so graphite reactors must be very large."
)

st.header("About this project")
st.markdown(
    "I built this for my TKS focus study on nuclear energy. It recreates the classic Monte Carlo model of neutron "
    "moderation and checks it against published values from "
    "[nuceng.ca](https://nuceng.ca/igna/thermal_reactors.htm). "
    "Simplifications: every energy after a bounce is treated as equally likely, and absorption is a fixed chance "
    "per collision based on each material's moderating ratio."
)
