import { useState, useEffect } from 'react'
import axios from 'axios'

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  // State for the new event form
  const [newEvent, setNewEvent] = useState({
    name: '',
    date: '',
    location: '',
    price: '',
    total_tickets: ''
  })

  // Function to fetch data from the server (Reusable)
  const fetchData = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/stats');
      setData(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data:", error);
      setLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchData();
  }, [])

  // Handle form input changes
  const handleInputChange = (e) => {
    setNewEvent({ ...newEvent, [e.target.name]: e.target.value });
  }

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent page reload
    try {
      await axios.post('http://127.0.0.1:8000/api/events', newEvent);

      // Clear form and refresh data
      setNewEvent({ name: '', date: '', location: '', price: '', total_tickets: '' });
      alert("Event added successfully! 🎉");
      fetchData(); // Reload the table
    } catch (error) {
      console.error("Error adding event:", error);
      alert("Failed to add event.");
    }
  }

  if (loading) return <div className="text-center mt-5">Loading Dashboard...</div>

  return (
    <div className="container mt-5 pb-5">
      <h1 className="text-center mb-5">🎉 PartyFlow Dashboard (React)</h1>

      {/* Analytics Cards */}
      <div className="row text-center mb-5">
        <div className="col-md-4">
          <div className="card p-3 shadow-sm border-0 bg-light">
            <h5 className="text-muted">💰 Revenue</h5>
            <h2 className="text-success">{data.stats.total_revenue} ₪</h2>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card p-3 shadow-sm border-0 bg-light">
            <h5 className="text-muted">🎟️ Tickets Sold</h5>
            <h2 className="text-primary">{data.stats.tickets_sold}</h2>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card p-3 shadow-sm border-0 bg-light">
            <h5 className="text-muted">🔥 Top Event</h5>
            <h2 className="text-danger">{data.stats.top_event}</h2>
          </div>
        </div>
      </div>

      {/* Add New Event Form */}
      <div className="card shadow mb-5">
        <div className="card-header bg-primary text-white">
          ➕ Add New Event
        </div>
        <div className="card-body">
          <form onSubmit={handleSubmit} className="row g-3">
            <div className="col-md-6">
              <label className="form-label">Event Name</label>
              <input type="text" name="name" className="form-control" value={newEvent.name} onChange={handleInputChange} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Date</label>
              <input type="text" name="date" className="form-control" placeholder="DD/MM/YYYY" value={newEvent.date} onChange={handleInputChange} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Location</label>
              <input type="text" name="location" className="form-control" value={newEvent.location} onChange={handleInputChange} required />
            </div>
            <div className="col-md-3">
              <label className="form-label">Price (₪)</label>
              <input type="number" name="price" className="form-control" value={newEvent.price} onChange={handleInputChange} required />
            </div>
            <div className="col-md-3">
              <label className="form-label">Total Tickets</label>
              <input type="number" name="total_tickets" className="form-control" value={newEvent.total_tickets} onChange={handleInputChange} required />
            </div>
            <div className="col-12 text-end">
              <button type="submit" className="btn btn-success px-4">Create Event</button>
            </div>
          </form>
        </div>
      </div>

      {/* Events Table */}
      <div className="card shadow">
        <div className="card-header bg-dark text-white">
          📋 Active Events
        </div>
        <div className="card-body">
          <table className="table table-hover">
            <thead>
              <tr>
                <th>Event Name</th>
                <th>Date</th>
                <th>Location</th>
                <th>Price</th>
                <th>Tickets</th>
              </tr>
            </thead>
            <tbody>
              {data.events.map((event) => (
                <tr key={event.id}>
                  <td>{event.name}</td>
                  <td>{event.date}</td>
                  <td>{event.location}</td>
                  <td>{event.price} ₪</td>
                  <td>{event.total_tickets}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default App