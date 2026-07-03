import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ApiError, api, Department, PatientCreate, PatientList } from "@/lib/api";
import { Button } from "@/components/core/Button";

interface AdmissionFormData {
  department_id: string;
  admission_type: string;
  admitted_at: string;
  length_of_stay: string;
  weight_kg: string;
  height_cm: string;
  chronic_conditions: string;
  num_previous_admissions: string;
  medications_count: string;
  last_hemoglobin: string;
  last_glucose: string;
  last_creatinine: string;
  procedures_count: string;
  smoking_status: string;
  alcohol_use: string;
  physical_activity: string;
  insurance_type: string;
  followup_compliance: string;
  social_support: string;
  mental_health_issue: string;
}

const EMPTY_PATIENT: PatientCreate = {
  mrn: "", first_name: "", last_name: "", dob: "", sex: "",
};

const EMPTY_ADMISSION: AdmissionFormData = {
  department_id: "", admission_type: "", admitted_at: "",
  length_of_stay: "", weight_kg: "", height_cm: "",
  chronic_conditions: "Hypertension", num_previous_admissions: "0",
  medications_count: "0", last_hemoglobin: "", last_glucose: "",
  last_creatinine: "", procedures_count: "0",
  smoking_status: "Never", alcohol_use: "Moderate",
  physical_activity: "Medium", insurance_type: "Private",
  followup_compliance: "Good", social_support: "Strong",
  mental_health_issue: "No",
};

const STEP_TITLES = ["Patient Identity", "This Admission", "Clinical Data"];

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-2">
      {children}
    </div>
  );
}

function computeBmi(weight: string, height: string): number | null {
  const w = parseFloat(weight);
  const h = parseFloat(height);
  if (!w || !h) return null;
  return Math.round((w / ((h / 100) ** 2)) * 10) / 10;
}

function computeAge(dob: string): number {
  if (!dob) return 0;
  return Math.floor((Date.now() - new Date(dob).getTime()) / (365.25 * 24 * 3600 * 1000));
}

export function PatientSearch() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [step, setStep] = useState(1);
  const [patientForm, setPatientForm] = useState<PatientCreate>(EMPTY_PATIENT);
  const [admForm, setAdmForm] = useState<AdmissionFormData>(EMPTY_ADMISSION);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["patients", q],
    queryFn: () => api.get<PatientList>(`/patients?q=${encodeURIComponent(q)}`),
  });

  const departments = useQuery({
    queryKey: ["departments"],
    queryFn: () => api.get<Department[]>("/patients/departments"),
    enabled: showModal,
  });

  const addPatient = useMutation({
    mutationFn: async () => {
      const patient = await api.post<{ id: string }>("/patients", patientForm);

      const bmi = computeBmi(admForm.weight_kg, admForm.height_cm);
      const age = computeAge(patientForm.dob);

      const features: Record<string, unknown> = {
        gender: patientForm.sex,
        age,
        admission_type: admForm.admission_type,
        length_of_stay: parseFloat(admForm.length_of_stay) || 0,
        num_previous_admissions: parseInt(admForm.num_previous_admissions) || 0,
        medications_count: parseInt(admForm.medications_count) || 0,
        procedures_count: parseInt(admForm.procedures_count) || 0,
        chronic_conditions: admForm.chronic_conditions,
        smoking_status: admForm.smoking_status,
        alcohol_use: admForm.alcohol_use,
        physical_activity: admForm.physical_activity,
        insurance_type: admForm.insurance_type,
        followup_compliance: admForm.followup_compliance,
        social_support: admForm.social_support,
        mental_health_issue: admForm.mental_health_issue,
      };
      if (admForm.weight_kg) features.weight_kg = parseFloat(admForm.weight_kg);
      if (admForm.height_cm) features.height_cm = parseFloat(admForm.height_cm);
      if (bmi !== null) features.bmi = bmi;
      if (admForm.last_hemoglobin) features.last_hemoglobin = parseFloat(admForm.last_hemoglobin);
      if (admForm.last_glucose) features.last_glucose = parseFloat(admForm.last_glucose);
      if (admForm.last_creatinine) features.last_creatinine = parseFloat(admForm.last_creatinine);

      await api.post(`/patients/${patient.id}/admissions`, {
        department_id: admForm.department_id,
        admission_type: admForm.admission_type,
        admitted_at: new Date(admForm.admitted_at + "T12:00:00").toISOString(),
        length_of_stay: parseFloat(admForm.length_of_stay) || 0,
        clinical_features: features,
      });

      return patient;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["patients"] });
      closeModal();
    },
    onError: (err: ApiError) => {
      if (err.status === 409) {
        setFormError(`MRN ${patientForm.mrn} already exists in your hospital.`);
        setStep(1);
      } else {
        setFormError(err.message);
      }
    },
  });

  function closeModal() {
    setShowModal(false);
    setStep(1);
    setPatientForm(EMPTY_PATIENT);
    setAdmForm(EMPTY_ADMISSION);
    setFormError(null);
  }

  function handleNext() {
    setFormError(null);
    if (step === 1) {
      if (!patientForm.mrn || !patientForm.first_name || !patientForm.last_name ||
          !patientForm.dob || !patientForm.sex) {
        setFormError("Please fill in all required fields.");
        return;
      }
      setStep(2);
    } else if (step === 2) {
      if (!admForm.department_id || !admForm.admission_type || !admForm.admitted_at ||
          !admForm.length_of_stay) {
        setFormError("Please fill in all required fields.");
        return;
      }
      setStep(3);
    } else {
      addPatient.mutate();
    }
  }

  const bmi = computeBmi(admForm.weight_kg, admForm.height_cm);

  const inputCls =
    "w-full px-3 py-2 text-sm border border-slate-300 rounded-md font-sans " +
    "focus:outline-none focus:shadow-focus focus:border-brand-600 bg-white";
  const labelCls = "block text-xs font-medium text-slate-600 mb-1";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-navy-700">Patients</h1>
          <p className="text-sm text-slate-500 mt-0.5">Search and manage admitted patients.</p>
        </div>
        <div className="flex gap-3">
          <input
            type="search"
            placeholder="Search MRN or name…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-300 rounded-md w-72 font-sans
                       focus:outline-none focus:shadow-focus focus:border-brand-600"
          />
          <Button variant="primary" onClick={() => setShowModal(true)}>
            + Add Patient
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">MRN</th>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">Name</th>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">DOB</th>
              <th className="text-left px-4 py-3 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">Sex</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr><td colSpan={5} className="p-8 text-center text-slate-400 text-sm">Loading…</td></tr>
            )}
            {!isLoading && data?.items.length === 0 && (
              <tr><td colSpan={5} className="p-8 text-center text-slate-400 text-sm">No patients found.</td></tr>
            )}
            {data?.items.map((p) => (
              <tr key={p.id} className="hover:bg-slate-50 cursor-pointer transition-colors duration-100">
                <td className="px-4 py-3 font-mono text-xs text-slate-500">{p.mrn}</td>
                <td className="px-4 py-3 font-medium text-slate-800">{p.last_name}, {p.first_name}</td>
                <td className="px-4 py-3 text-slate-600">{p.dob}</td>
                <td className="px-4 py-3 text-slate-600">{p.sex}</td>
                <td className="px-4 py-3 text-right">
                  <Link to={`/patients/${p.id}`} className="text-brand-600 hover:text-brand-700 text-xs font-medium">
                    Open chart →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && (
          <div className="px-4 py-2 border-t border-slate-100 bg-slate-50 text-xs text-slate-400">
            Showing {data.items.length} of {data.total} patients
          </div>
        )}
      </div>

      {/* ── Add Patient Modal ─────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[92vh] flex flex-col">

            {/* Header + step indicator */}
            <div className="px-6 pt-6 pb-5 border-b border-slate-100 shrink-0">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="font-display text-lg font-semibold text-navy-700">Add New Patient</h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Step {step} of 3 — {STEP_TITLES[step - 1]}
                  </p>
                </div>
                <button
                  onClick={closeModal}
                  className="text-slate-400 hover:text-slate-600 transition-colors text-2xl leading-none mt-0.5"
                >
                  ×
                </button>
              </div>

              {/* Stepper */}
              <div className="flex items-center">
                {STEP_TITLES.map((title, i) => {
                  const s = i + 1;
                  const done = s < step;
                  const active = s === step;
                  return (
                    <div key={s} className={`flex items-center ${s < 3 ? "flex-1" : ""}`}>
                      <div className="flex items-center gap-2 shrink-0">
                        <div className={[
                          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-all",
                          done ? "bg-brand-600 text-white" :
                          active ? "bg-brand-600 text-white ring-2 ring-brand-100" :
                          "bg-slate-100 text-slate-400",
                        ].join(" ")}>
                          {done ? "✓" : s}
                        </div>
                        <span className={[
                          "text-xs hidden sm:block",
                          active ? "text-brand-600 font-medium" :
                          done ? "text-slate-500" : "text-slate-400",
                        ].join(" ")}>
                          {title}
                        </span>
                      </div>
                      {s < 3 && (
                        <div className={`flex-1 h-px mx-3 ${s < step ? "bg-brand-400" : "bg-slate-200"}`} />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Scrollable body */}
            <div className="overflow-y-auto flex-1 px-6 py-5">

              {/* ── Step 1: Patient Identity ── */}
              {step === 1 && (
                <div className="space-y-4">
                  <div>
                    <label className={labelCls}>MRN <span className="text-risk-high">*</span></label>
                    <input
                      className={inputCls}
                      placeholder="e.g. MRN-00123"
                      value={patientForm.mrn}
                      onChange={(e) => setPatientForm({ ...patientForm, mrn: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={labelCls}>First name <span className="text-risk-high">*</span></label>
                      <input
                        className={inputCls}
                        value={patientForm.first_name}
                        onChange={(e) => setPatientForm({ ...patientForm, first_name: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className={labelCls}>Last name <span className="text-risk-high">*</span></label>
                      <input
                        className={inputCls}
                        value={patientForm.last_name}
                        onChange={(e) => setPatientForm({ ...patientForm, last_name: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={labelCls}>Date of birth <span className="text-risk-high">*</span></label>
                      <input
                        type="date"
                        className={inputCls}
                        value={patientForm.dob}
                        onChange={(e) => setPatientForm({ ...patientForm, dob: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className={labelCls}>Sex <span className="text-risk-high">*</span></label>
                      <select
                        className={inputCls}
                        value={patientForm.sex}
                        onChange={(e) => setPatientForm({ ...patientForm, sex: e.target.value })}
                      >
                        <option value="">Select…</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* ── Step 2: Admission ── */}
              {step === 2 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={labelCls}>Department <span className="text-risk-high">*</span></label>
                      <select
                        className={inputCls}
                        value={admForm.department_id}
                        onChange={(e) => setAdmForm({ ...admForm, department_id: e.target.value })}
                      >
                        <option value="">
                          {departments.isLoading ? "Loading…" : "Select department…"}
                        </option>
                        {departments.data?.map((d) => (
                          <option key={d.id} value={d.id}>{d.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className={labelCls}>Admission type <span className="text-risk-high">*</span></label>
                      <select
                        className={inputCls}
                        value={admForm.admission_type}
                        onChange={(e) => setAdmForm({ ...admForm, admission_type: e.target.value })}
                      >
                        <option value="">Select…</option>
                        <option value="Emergency">Emergency</option>
                        <option value="Urgent">Urgent</option>
                        <option value="Elective">Elective</option>
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={labelCls}>Admission date <span className="text-risk-high">*</span></label>
                      <input
                        type="date"
                        className={inputCls}
                        value={admForm.admitted_at}
                        onChange={(e) => setAdmForm({ ...admForm, admitted_at: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className={labelCls}>Length of stay (days) <span className="text-risk-high">*</span></label>
                      <input
                        type="number"
                        min="0"
                        step="1"
                        className={inputCls}
                        placeholder="e.g. 4"
                        value={admForm.length_of_stay}
                        onChange={(e) => setAdmForm({ ...admForm, length_of_stay: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className={labelCls}>Weight (kg)</label>
                      <input
                        type="number"
                        min="0"
                        step="0.1"
                        className={inputCls}
                        placeholder="e.g. 72"
                        value={admForm.weight_kg}
                        onChange={(e) => setAdmForm({ ...admForm, weight_kg: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className={labelCls}>Height (cm)</label>
                      <input
                        type="number"
                        min="0"
                        step="1"
                        className={inputCls}
                        placeholder="e.g. 170"
                        value={admForm.height_cm}
                        onChange={(e) => setAdmForm({ ...admForm, height_cm: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className={labelCls}>BMI (auto)</label>
                      <div className="px-3 py-2 text-sm border border-slate-200 rounded-md bg-slate-50 font-mono text-slate-500">
                        {bmi !== null ? bmi.toFixed(1) : "—"}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── Step 3: Clinical Data ── */}
              {step === 3 && (
                <div>
                  <SectionLabel>Lab Values</SectionLabel>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className={labelCls}>Hemoglobin (g/dL)</label>
                      <input
                        type="number"
                        step="0.1"
                        className={inputCls}
                        placeholder="e.g. 13.5"
                        value={admForm.last_hemoglobin}
                        onChange={(e) => setAdmForm({ ...admForm, last_hemoglobin: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className={labelCls}>Glucose (mg/dL)</label>
                      <input
                        type="number"
                        step="1"
                        className={inputCls}
                        placeholder="e.g. 110"
                        value={admForm.last_glucose}
                        onChange={(e) => setAdmForm({ ...admForm, last_glucose: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className={labelCls}>Creatinine (mg/dL)</label>
                      <input
                        type="number"
                        step="0.01"
                        className={inputCls}
                        placeholder="e.g. 1.0"
                        value={admForm.last_creatinine}
                        onChange={(e) => setAdmForm({ ...admForm, last_creatinine: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="mt-5">
                    <SectionLabel>Medical History</SectionLabel>
                    <div className="space-y-3">
                      <div>
                        <label className={labelCls}>Chronic condition</label>
                        <select
                          className={inputCls}
                          value={admForm.chronic_conditions}
                          onChange={(e) => setAdmForm({ ...admForm, chronic_conditions: e.target.value })}
                        >
                          <option value="None">None</option>
                          <option value="Hypertension">Hypertension</option>
                          <option value="Diabetes">Diabetes</option>
                          <option value="Heart Disease">Heart Disease</option>
                          <option value="COPD">COPD</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <label className={labelCls}>Previous admissions</label>
                          <input
                            type="number"
                            min="0"
                            step="1"
                            className={inputCls}
                            value={admForm.num_previous_admissions}
                            onChange={(e) => setAdmForm({ ...admForm, num_previous_admissions: e.target.value })}
                          />
                        </div>
                        <div>
                          <label className={labelCls}>Medications count</label>
                          <input
                            type="number"
                            min="0"
                            step="1"
                            className={inputCls}
                            value={admForm.medications_count}
                            onChange={(e) => setAdmForm({ ...admForm, medications_count: e.target.value })}
                          />
                        </div>
                        <div>
                          <label className={labelCls}>Procedures count</label>
                          <input
                            type="number"
                            min="0"
                            step="1"
                            className={inputCls}
                            value={admForm.procedures_count}
                            onChange={(e) => setAdmForm({ ...admForm, procedures_count: e.target.value })}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-5">
                    <SectionLabel>Lifestyle & Social</SectionLabel>
                    <div className="space-y-3">
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <label className={labelCls}>Smoking status</label>
                          <select
                            className={inputCls}
                            value={admForm.smoking_status}
                            onChange={(e) => setAdmForm({ ...admForm, smoking_status: e.target.value })}
                          >
                            <option value="Never">Never</option>
                            <option value="Former">Former</option>
                            <option value="Current">Current</option>
                          </select>
                        </div>
                        <div>
                          <label className={labelCls}>Alcohol use</label>
                          <select
                            className={inputCls}
                            value={admForm.alcohol_use}
                            onChange={(e) => setAdmForm({ ...admForm, alcohol_use: e.target.value })}
                          >
                            <option value="None">None</option>
                            <option value="Moderate">Moderate</option>
                            <option value="High">High</option>
                          </select>
                        </div>
                        <div>
                          <label className={labelCls}>Physical activity</label>
                          <select
                            className={inputCls}
                            value={admForm.physical_activity}
                            onChange={(e) => setAdmForm({ ...admForm, physical_activity: e.target.value })}
                          >
                            <option value="Low">Low</option>
                            <option value="Medium">Medium</option>
                            <option value="High">High</option>
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className={labelCls}>Insurance type</label>
                          <select
                            className={inputCls}
                            value={admForm.insurance_type}
                            onChange={(e) => setAdmForm({ ...admForm, insurance_type: e.target.value })}
                          >
                            <option value="Private">Private</option>
                            <option value="Public">Public</option>
                          </select>
                        </div>
                        <div>
                          <label className={labelCls}>Follow-up compliance</label>
                          <select
                            className={inputCls}
                            value={admForm.followup_compliance}
                            onChange={(e) => setAdmForm({ ...admForm, followup_compliance: e.target.value })}
                          >
                            <option value="Good">Good</option>
                            <option value="Poor">Poor</option>
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className={labelCls}>Social support</label>
                          <select
                            className={inputCls}
                            value={admForm.social_support}
                            onChange={(e) => setAdmForm({ ...admForm, social_support: e.target.value })}
                          >
                            <option value="Strong">Strong</option>
                            <option value="Weak">Weak</option>
                          </select>
                        </div>
                        <div>
                          <label className={labelCls}>Mental health issue</label>
                          <select
                            className={inputCls}
                            value={admForm.mental_health_issue}
                            onChange={(e) => setAdmForm({ ...admForm, mental_health_issue: e.target.value })}
                          >
                            <option value="No">No</option>
                            <option value="Yes">Yes</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

            </div>

            {/* Footer nav */}
            <div className="px-6 py-4 border-t border-slate-100 shrink-0 flex items-center justify-between gap-4">
              <Button
                variant="ghost"
                disabled={addPatient.isPending}
                onClick={step === 1 ? closeModal : () => { setFormError(null); setStep((s) => s - 1); }}
              >
                {step === 1 ? "Cancel" : "← Back"}
              </Button>

              {formError && (
                <p className="text-sm text-risk-high flex-1 text-center">{formError}</p>
              )}

              <Button
                variant="primary"
                loading={addPatient.isPending}
                onClick={handleNext}
              >
                {step === 3 ? "Add Patient" : "Continue →"}
              </Button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
