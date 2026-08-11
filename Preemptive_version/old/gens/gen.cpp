//对于每组 i<j 独立的 p 的概率有一条 (i,j) 的边（p 精确到小数点3位）
//所有 C_{n}^{n_t} 种点的类型情况等概率出现
//每个点耗时在 [1,1000] 等概率随机
#include<bits/stdc++.h>
using namespace std;
int n,m,n_t;
double p;
auto seed = std::chrono::high_resolution_clock::now()
                .time_since_epoch()
                .count();
std::mt19937 rng(static_cast<unsigned>(seed));
pair<int,int> edge[10000007];
int main(int argc, char* argv[])
{
    if(argc < 5) {
        cerr << "Usage: " << argv[0] << " <n> <n_t> <p> <out_loc> [T]" << endl;
        return 1;
    }
    n = stoi(argv[1]);
    n_t = stoi(argv[2]);
    p = stod(argv[3]);
    string out_loc = argv[4];

    freopen(out_loc.c_str(), "w", stdout);
    int n_c = n - n_t;

    for(int i=1;i<=n;i++){
        for(int j=i+1;j<=n;j++){
            if(rng()%1000<1000*p){
                edge[++m]={i,j};
                if(m > 10000000) {
                    cerr << "Error: Number of edges exceeds limit of 10^7." << endl;
                    return 1;
                }
            }
        }
    }

    cout<<n<<" "<<m<<"\n";

    for(int i = 1; i <= n; ++i) {
        char c = (rng()%(n_t+n_c) < n_c ? 'c' : 't');
        if(c == 'c') n_c--;
        else n_t--;
        int w = rand() % 1000 + 1;
        cout << c << " " << w << endl;
    }

    for(int i=1;i<=m;i++) cout<<edge[i].first<<" "<<edge[i].second<<"\n";
    return 0;
}