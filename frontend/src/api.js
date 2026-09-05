const API_URL = "http://127.0.0.1:8000"

async function request(endpoint, method = "GET", body = null) {
    const options = { method }
    if (body) {
        options.headers = { "Content-Type": "application/json" }
        options.body = JSON.stringify(body)
    }

    const response = await fetch(`${API_URL}${endpoint}`, options)

    if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`API Error (${response.status}): ${errorText || response.statusText}`)
    }

    return response.json()
}

export async function getDashboard() {
    return request("/api/dashboard")
}

export async function getMetrics() {
    return request("/api/metrics")
}

export async function getTransactions() {
    return request("/api/transactions")
}

export async function getDecisions() {
    return request("/api/decisions")
}

export async function getExecution() {
    return request("/api/execution")
}

export async function getAudit() {
    return request("/api/audit")
}

export async function getRisk() {
    return request("/api/risk")
}

export async function predictRecovery(transaction) {
    return request("/api/recovery/predict", "POST", transaction)
}

export async function evaluateRecovery() {
    return request("/api/recovery/evaluate", "POST")
}

// --- Recovery Cases ---

export async function getRecoveryCases(caseType = null, status = null) {
    const params = new URLSearchParams()
    if (caseType) params.append("case_type", caseType)
    if (status) params.append("status", status)
    const qs = params.toString()
    return request(`/api/recovery/cases${qs ? "?" + qs : ""}`)
}

export async function getRecoveryCaseById(caseId) {
    return request(`/api/recovery/cases/${encodeURIComponent(caseId)}`)
}

export async function getBatchMetrics() {
    return request("/api/recovery/batch-metrics")
}

// Authoritative live recovery metrics (sourced from recovery_cases.json)
export async function getRecoveryMetrics() {
    return request("/api/recovery/metrics")
}

export async function executeRecoveryCase(caseInput) {
    return request("/api/recovery/cases/execute", "POST", caseInput)
}

// --- Communication ---

export async function sendCommunication(transaction) {
    return request("/api/communication/send", "POST", { transaction })
}

// --- Recovery Execute (orchestrated) ---

export async function executeRecovery(transaction) {
    return request("/api/recovery/execute", "POST", transaction)
}

// --- Payment ---

export async function createPayment(body) {
    return request("/api/payment/create", "POST", body)
}

export async function retryPayment(body) {
    return request("/api/payment/retry", "POST", body)
}

export async function getPaymentStatus(transactionId) {
    return request(`/api/payment/status/${encodeURIComponent(transactionId)}`)
}
