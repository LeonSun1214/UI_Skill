import Card from './components/Card/Card';
import Button from './components/Button/Button';
import Header from './components/Header/Header';

export default function App() {
  return (
    <div className="page">
      <Header />
      <h1 className="page-title">Recipes</h1>
      <Card title="Bread">Flour, water, salt, time.</Card>
      <Button>Add a recipe</Button>
    </div>
  );
}
