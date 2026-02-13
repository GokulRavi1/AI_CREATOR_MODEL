import { AppProvider, useApp } from './context/AppContext';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Toasts from './components/Layout/Toasts';
import IdentityLab from './components/IdentityLab/IdentityLab';
import ContentStudio from './components/ContentStudio/ContentStudio';
import SystemStatus from './components/SystemStatus';
import HistoryPanel from './components/History/HistoryPanel';

function MainLayout() {
  return (
    <div className="app-shell">
      <Header />
      <main className="app-main">
        <Sidebar />
        <section className="output-panel">
          <ContentArea />
        </section>
      </main>
      <Toasts />
    </div>
  );
}

function ContentArea() {
  const { activeTab } = useApp();

  return (
    <div className="h-full">
      {activeTab === 'identity' ? (
        <IdentityLab />
      ) : activeTab === 'history' ? (
        <HistoryPanel />
      ) : activeTab === 'studio' ? (
        <ContentStudio />
      ) : (
        <SystemStatus />
      )}
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <MainLayout />
    </AppProvider>
  );
}

export default App;
