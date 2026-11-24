// Runs once the page has loaded and connects the forms and buttons to the API.
document.addEventListener('DOMContentLoaded', () => {
    // Grab the page elements we need.
    const messageContainer = document.getElementById('message-container');
    const addOrderForm = document.getElementById('add-order-form');
    const getOrderForm = document.getElementById('get-order-form');
    const singleOrderDetails = document.getElementById('single-order-details');
    const updateStatusForm = document.getElementById('update-status-form');
    const listAllOrdersBtn = document.getElementById('list-all-orders-btn');
    const filterStatusSelect = document.getElementById('filter-status');
    const ordersTableBody = document.getElementById('orders-table-body');

    // Shows a green (success) or red (error) message that hides after 5 seconds.
    function showMessage(message, type) {
        messageContainer.textContent = message;
        messageContainer.className = `message-box ${type === 'success' ? 'message-success' : 'message-error'}`;
        messageContainer.classList.remove('hidden');
        setTimeout(() => messageContainer.classList.add('hidden'), 5000);
    }

    // Fills the orders table, or shows "No orders to display." if the list is empty.
    function renderOrdersTable(orders) {
        ordersTableBody.innerHTML = '';
        if (orders.length === 0) {
            ordersTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4">No orders to display.</td></tr>';
            return;
        }
        orders.forEach(order => {
            const row = document.createElement('tr');
            row.innerHTML = `<td class="p-2">${order.order_id}</td><td class="p-2">${order.item_name}</td><td class="p-2">${order.quantity}</td><td class="p-2">${order.customer_id}</td><td class="p-2 capitalize">${order.status}</td>`;
            ordersTableBody.appendChild(row);
        });
    }

    // Loads orders from the API (only one status if given) and shows them in the table.
    async function fetchAndRenderOrders(status = '') {
        try {
            const url = status ? `/api/orders?status=${status}` : '/api/orders';
            const response = await fetch(url);
            const orders = await response.json();
            if (!response.ok) throw new Error(orders.error || 'Unknown error');
            renderOrdersTable(orders);
        } catch (error) { showMessage(`Failed to load orders: ${error.message}`, 'error'); renderOrdersTable([]); }
    }

    // "Add New Order" form: sends the order to POST /api/orders, then refreshes the table.
    addOrderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(addOrderForm);
        const orderData = Object.fromEntries(formData.entries());
        orderData.quantity = parseInt(orderData.quantity);
        try {
            const response = await fetch('/api/orders', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(orderData) });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);
            showMessage(`Order ${result.order_id} added!`, 'success');
            addOrderForm.reset();
            fetchAndRenderOrders();
        } catch (error) { showMessage(`Failed to add order: ${error.message}`, 'error'); }
    });

    // "Get Order Details" form: fetches GET /api/orders/<id> and shows the order's JSON.
    getOrderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const orderId = document.getElementById('get-order-id').value.trim();
        singleOrderDetails.classList.add('hidden');
        if (!orderId) { showMessage('Please enter an Order ID.', 'error'); return; }
        try {
            const response = await fetch(`/api/orders/${orderId}`);
            const order = await response.json();
            if (!response.ok) throw new Error(order.error);
            singleOrderDetails.querySelector('pre').textContent = JSON.stringify(order, null, 2);
            singleOrderDetails.classList.remove('hidden');
        } catch (error) { showMessage(`Failed to get order: ${error.message}`, 'error'); }
    });

    // "Update Order Status" form: sends PUT /api/orders/<id>/status, then refreshes the table.
    updateStatusForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const orderId = document.getElementById('update-order-id').value.trim();
        const newStatus = document.getElementById('update-new-status').value;
        if (!orderId || !newStatus) { showMessage('Please enter an Order ID and select a new status.', 'error'); return; }
        try {
            const response = await fetch(`/api/orders/${orderId}/status`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_status: newStatus }) });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);
            showMessage(`Order ${orderId} status updated.`, 'success');
            updateStatusForm.reset();
            fetchAndRenderOrders();
        } catch (error) { showMessage(`Failed to update status: ${error.message}`, 'error'); }
    });

    // "Refresh" button: clears the status filter and reloads every order.
    listAllOrdersBtn.addEventListener('click', () => { filterStatusSelect.value = ''; fetchAndRenderOrders(); });
    // Status filter dropdown: reloads the table with only orders in that status.
    filterStatusSelect.addEventListener('change', (e) => fetchAndRenderOrders(e.target.value));
    // Load the orders table as soon as the page opens.
    fetchAndRenderOrders();
});
