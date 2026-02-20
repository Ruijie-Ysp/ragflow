import { Outlet } from 'umi';
import { Header } from './next-header';

export default function NextLayout() {
  return (
    <section className="h-screen flex flex-col overflow-hidden">
      <Header></Header>
      <main className="flex-1 min-h-0 overflow-hidden">
        <Outlet />
      </main>
    </section>
  );
}
