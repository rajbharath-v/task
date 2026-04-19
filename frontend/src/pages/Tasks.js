import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { getTasks, createTask, updateTask, deleteTask } from "../api/api";
import { useNavigate } from "react-router-dom";

export default function Tasks() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [tasks, setTasks] = useState([]);
  const [meta, setMeta] = useState({ total: 0, page: 1, total_pages: 1 });
  const [filter, setFilter] = useState(null); // null=all, true=completed, false=pending
  const [page, setPage] = useState(1);

  const [newTask, setNewTask] = useState({ title: "", description: "" });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const [loading, setLoading] = useState(false);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTasks(page, filter);
      setTasks(res.data.tasks);
      setMeta({ total: res.data.total, page: res.data.page, total_pages: res.data.total_pages });
    } catch {
      // token expired
      logout();
      navigate("/login");
    } finally {
      setLoading(false);
    }
  }, [page, filter, logout, navigate]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newTask.title.trim()) return;
    setCreateError("");
    setCreating(true);
    try {
      await createTask(newTask);
      setNewTask({ title: "", description: "" });
      setPage(1);
      fetchTasks();
    } catch (err) {
      setCreateError(err.response?.data?.detail || "Failed to create task");
    } finally {
      setCreating(false);
    }
  };

  const handleToggle = async (task) => {
    try {
      await updateTask(task.id, { completed: !task.completed });
      fetchTasks();
    } catch {}
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this task?")) return;
    try {
      await deleteTask(id);
      fetchTasks();
    } catch {}
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const filterLabel = filter === null ? "All" : filter ? "Completed" : "Pending";

  return (
    <div className="tasks-container">
      {/* Header */}
      <div className="tasks-header">
        <h1>Task Manager</h1>
        <div className="header-right">
          <span className="username">Hi, {user?.username}</span>
          <button className="btn-logout" onClick={handleLogout}>Logout</button>
        </div>
      </div>

      {/* Create Task Form */}
      <div className="card create-form">
        <h3>New Task</h3>
        <form onSubmit={handleCreate}>
          <input
            type="text"
            placeholder="Task title *"
            required
            value={newTask.title}
            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
          />
          {createError && <p className="error">{createError}</p>}
          <button type="submit" disabled={creating}>
            {creating ? "Adding..." : "Add Task"}
          </button>
        </form>
      </div>

      {/* Filter Bar */}
      <div className="filter-bar">
        <span>Filter: </span>
        {[null, false, true].map((val, i) => {
          const label = val === null ? "All" : val ? "Completed" : "Pending";
          return (
            <button
              key={i}
              className={`btn-filter ${filter === val ? "active" : ""}`}
              onClick={() => { setFilter(val); setPage(1); }}
            >
              {label}
            </button>
          );
        })}
        <span className="total-count">{meta.total} task{meta.total !== 1 ? "s" : ""}</span>
      </div>

      {/* Task List */}
      {loading ? (
        <p className="center-text">Loading...</p>
      ) : tasks.length === 0 ? (
        <p className="center-text">No tasks found. {filter !== null && <span>Try changing the filter.</span>}</p>
      ) : (
        <div className="task-list">
          {tasks.map((task) => (
            <div key={task.id} className={`task-card ${task.completed ? "completed" : ""}`}>
              <div className="task-main">
                <input
                  type="checkbox"
                  checked={task.completed}
                  onChange={() => handleToggle(task)}
                  title="Mark as completed"
                />
                <div className="task-info">
                  <p className="task-title">{task.title}</p>
                  {task.description && <p className="task-desc">{task.description}</p>}
                  <p className="task-meta">
                    {task.completed ? "✓ Completed" : "Pending"} · Created {new Date(task.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <button className="btn-delete" onClick={() => handleDelete(task.id)}>Delete</button>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {meta.total_pages > 1 && (
        <div className="pagination">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</button>
          <span>Page {meta.page} of {meta.total_pages}</span>
          <button disabled={page >= meta.total_pages} onClick={() => setPage(page + 1)}>Next →</button>
        </div>
      )}
    </div>
  );
}
